import datetime
from workflow.types import WorkflowNode, SourceType, AuditWorkflow, NodeFailure, AuditReport

'''The api will recieves the frontend request with the source name and the type to audit.
This node will handle the scanning phase of the workflow, where it will route to either the db agent,
file agent, or s3 buckets agent to get the scanned details of the given datasource'''

class ScanNode(WorkflowNode):
    '''this will call a predefined tool sequence to output the source report'''
    name = "scan"

    def __init__(self, db_agent, file_agent=None, s3_agent=None):
        '''inject dependencies through the constructor on runtime'''
        self._agents = {
            SourceType.DATABASE: db_agent,
            SourceType.FILE:     file_agent,
            SourceType.S3:       s3_agent,
        }

    async def run(self, state: AuditWorkflow) -> AuditWorkflow:
        
        source_type = state.job.source_type
        agent = self._agents.get(source_type)
 
        if agent is None:
            raise NodeFailure(self.name,
                f"No discovery agent registered for source type '{source_type}'")
 
        state.scan_report = await agent.get_source_report(state.job)
 
        if not state.scan_report.tables:
            raise NodeFailure(self.name,
                f"Discovery returned no tables for source '{state.job.source_name}'")
 
        return state


'''Given a source report, this node will generate a classification report highlighting 
whether the information category is PII, Quasi PII, or Safe '''
class ClassifierNode(WorkflowNode):
    """
    Passes each column through the classification agent (LLM + RAG).
    Every column in every table is classified.
    """
 
    name = "classification"
 
    def __init__(self, classification_agent):
        self.agent = classification_agent
 
    async def run(self, state: AuditWorkflow) -> AuditWorkflow:
        if state.scan_report is None:
            raise NodeFailure(self.name, "scan_report is missing — discovery must run first")
 
        state.classified_report = await self.agent.get_classification_report(
            scan_report=state.scan_report,
            frameworks=state.job.frameworks,
        )
        return state

class PolicyNode(WorkflowNode):
    """
    Runs checks against the classified report and get violation report based on proposed workflows
    """
 
    name = "policy_check"
 
    def __init__(self, policy_agent):
        self.agent = policy_agent
 
    async def run(self, state: AuditWorkflow) -> AuditWorkflow:
        if state.classified_report is None:
            raise NodeFailure(self.name,
                "classified_report is missing — classification must run first")
 
        state.violation_report = await self.agent.get_violation_report(
            classified_report=state.classified_report,
            scan_report=state.scan_report,        # needed for structural checks
            frameworks=state.job.frameworks,
        )
        return state
    
class RemediationNode(WorkflowNode):
    """
    For every violation, proposes a remediation action.
    """
 
    name = "remediation"
 
    def __init__(self, remediation_agent):
        self.agent = remediation_agent
 
    async def run(self, context: AuditWorkflow) -> AuditWorkflow:
        if context.violation_report is None:
            raise NodeFailure(self.name,
                "violation_report is missing — policy check must run first")
 
        context.remediation_report = await self.agent.remediate(
            violation_report=context.violation_report,
            frameworks=context.job.frameworks,
        )
        return context

"Assemble all the previous reports into an audit report"
class AssembleNode(WorkflowNode):
    """Assembles all previous step outputs into a single AuditReport with a summary"""
 
    name = "report_assembly"
 
    def __init__(self, ollama_client):
        self.ollama_client = ollama_client
 
    async def run(self, state: AuditWorkflow) -> AuditWorkflow:

        summary = self._generate_summary(state)
 
        state.audit_report = AuditReport(
            audit_id           = state.job.job_id,
            source_id          = state.job.source_id,
            source_name        = state.job.source_name,
            source_type        = state.job.source_type,
            frameworks         = state.job.frameworks,
            scan_report        = state.scan_report,
            classified_report  = state.classified_report,
            violation_report   = state.violation_report,
            remediation_report = state.remediation_report,
            started_at         = state.job.created_at,
            completed_at       = datetime.datetime.now(),
            summary            = summary,
        )
 
        return state
 
    async def _generate_summary(self, state: AuditWorkflow) -> str:
        vr = state.violation_report
        rr = state.remediation_report
        prompt = f"""You are a data governance expert. Write a concise 3-sentence executive 
                 summary for a compliance audit report. Be direct and factual.
 
                Source: {state.job.source_name} ({state.job.source_type})
                Frameworks: {', '.join(state.job.frameworks)}
                violations: {vr.critical_count} critical, {vr.high_count} high, {vr.medium_count} medium
                Remediations: {rr.remediations}
 
                Write the summary now:"""
 
        response = await self.ollama_client.chat(
            model="qwen2.5:7b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        return response.choices.message.strip()
    
