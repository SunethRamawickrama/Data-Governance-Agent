import json
from datetime import datetime
from ollama import AsyncClient
from services.RAG_service.vector_store import vector_store
from workflow.types import (
    ViolationReport, Violation,
    RemediationReport, Remediation, RemediationType
)

REMEDIATION_PROMPT = """You are a data privacy compliance expert recommending fixes for policy violations.

You will be given a violation and relevant policy excerpts.
Recommend a concrete remediation for this violation.

Respond ONLY with a JSON object in this exact format:
{
  "remediation_type": "REDACT" | "ENCRYPT" | "RESTRICT" | "FIX_RETENTION_POLICY"| "FIX_ACCESS_CONTROL",
  "policy_basis": "which policy is violated and why it must be fixed",
  "recommended_solution": "concrete step-by-step action to resolve this violation"
}

No extra text. No markdown. Just the JSON object."""


class RemediationAgent:

    def __init__(self, model: str = "qwen2.5:7b"):
        self.llm   = AsyncClient()
        self.model = model

    async def remediate(
        self,
        violation_report: ViolationReport,
        frameworks: list[str],
    ) -> RemediationReport:

        remediations: list[Remediation] = []

        for violation in violation_report.violations:
            remediation = await self._remediate_violation(violation, frameworks)
            if remediation:
                remediations.append(remediation)

        return RemediationReport(
            source_id=violation_report.source_id,
            remediations=remediations,
            generated_at=datetime.now(),
        )

    async def _remediate_violation(
        self,
        violation: Violation,
        frameworks: list[str],
    ) -> Remediation | None:

        # retrieve policy chunks about fixing this specific rule
        policy_docs = vector_store.search(
            f"remediation fix for {violation.rule} {violation.framework} {' '.join(frameworks)}", k=3
        )
        policy_context = "\n\n".join([
            f"[{doc.metadata.get('source', 'unknown')} — page {doc.metadata.get('page_number', '?')}]\n{doc.page_content}"
            for doc in policy_docs
        ])

        user_prompt = f"""Recommend a remediation for this compliance violation.

        Table: {violation.table_name}
        Affected columns: {violation.affected_columns or 'entire table (metadata violation)'}
        Severity: {violation.severity.value}
        Rule violated: {violation.rule}
        Framework: {violation.framework}

        Relevant policy excerpts:
        {policy_context}

        Recommend remediation now:"""

        response = await self.llm.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": REMEDIATION_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            options={"temperature": 0.0},
        )

        raw = response["message"]["content"].strip()
        return self._parse_remediation(raw, violation)

    def _parse_remediation(self, raw: str, violation: Violation) -> Remediation | None:
        try:
            clean = raw.strip().removeprefix("```json").removesuffix("```").strip()
            data  = json.loads(clean)

            return Remediation(
                violation_id        =violation.violation_id,
                remediation_type    =RemediationType(data["remediation_type"]),
                affected_columns    =violation.affected_columns,
                table_name          =violation.table_name,
                policy_basis        =data["policy_basis"],
                recommended_solution=data["recommended_solution"],
            )

        except (Exception):
            return None  