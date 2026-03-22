from workflow.nodes import WorkflowNode, ScanNode, ClassifierNode, PolicyNode, RemediationNode, AssembleNode, AuditWorkflow, NodeFailure
from workflow.types import AuditJob, AuditReport

class AuditPipeline:
    """
    Deterministic pipeline runner.
    Executes nodes in a fixed sequence
    """
 
    def __init__(
        self,
        db_agent,
        classification_agent,
        policy_agent,
        remediation_agent,
        ollama_client,
        file_agent=None,
        s3_agent=None,
    ):
        self.nodes: list[WorkflowNode] = [
            ScanNode(db_agent, file_agent, s3_agent),
            ClassifierNode(classification_agent),
            PolicyNode(policy_agent),
            RemediationNode(remediation_agent),
            AssembleNode(ollama_client),
        ]
 
    async def run(self, job: AuditJob) -> AuditReport:
        state = AuditWorkflow(job=job)
 
        for node in self.nodes:
            try:
                state = await node.run(state)
            except NodeFailure as e:
                state.failed_at_node = e.node_name
                state.error          = e.reason
                raise
 
        return state.audit_report
 