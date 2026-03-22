from workflow.nodes import WorkflowNode, ScanNode, ClassifierNode, PolicyNode, RemediationNode, AssembleNode, AuditWorkflow, NodeFailure
from workflow.types import AuditJob, AuditReport
from agents.sub_agents import classification_agent, policy_agent, remedition_agent
from agents.sub_agents.db_agent import get_db_agent
from ollama import Client
from datetime import datetime
import uuid

class AuditPipeline:
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

    async def audit(
        self,
        source_name: str,
        source_type: str,
        frameworks: list[str] = ["GDPR", "CCPA"]
    ) -> AuditReport:
        job = AuditJob(
            job_id      =str(uuid.uuid4()),
            source_id   =str(uuid.uuid4()),
            source_name =source_name,
            source_type =source_type,
            frameworks  =frameworks,
            created_at  =datetime.now(),
        )
        return await self.run(job)


async def create_pipeline() -> AuditPipeline:
    """
    Async factory - call at startup to get a ready pipeline.
    """
    db_agent = await get_db_agent() 

    return AuditPipeline(
        db_agent            =db_agent,
        classification_agent=classification_agent.ClassificationAgent(),
        policy_agent        =policy_agent.PolicyAgent(),
        remediation_agent   =remedition_agent.RemediationAgent(),
        ollama_client       =Client(),
    )