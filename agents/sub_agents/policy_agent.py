import json
import uuid
from datetime import datetime
from ollama import AsyncClient
from services.RAG_service.vector_store import vector_store
from workflow.types import (
    ClassifiedReport, ClassifiedTable, ClassifiedColumn,
    SourceScanReport, ViolationReport, Violation,
    Classification, Severity
)

POLICY_CHECK_PROMPT = """You are a data privacy compliance expert.

You will be given information about a database table and its governance metadata,
or a specific PII column and its classification details.

Determine if there is a compliance violation. Return ONLY a JSON array of violations found.
Each violation must follow this format:
{
  "severity": "CRITICAL" | "HIGH" | "MEDIUM",
  "rule": "exact rule citation e.g. GDPR Art. 5.1.e — Storage Limitation",
  "affected_columns": ["column_name"] or [] if metadata violation,
  "framework": "GDPR" | "CCPA"
}

If no violations found, return an empty array: []

No extra text. No markdown. Just the JSON array."""


class PolicyAgent:

    def __init__(self, model: str = "qwen2.5:7b"):
        self.llm   = AsyncClient()
        self.model = model

    async def get_violation_report(
        self,
        classified_report: ClassifiedReport,
        scan_report: SourceScanReport,
        frameworks: list[str],
    ) -> ViolationReport:

        # build metadata lookup from scan_report
        metadata_lookup = {
            table.table_name: table.metadata
            for table in scan_report.tables
        }

        all_violations: list[Violation] = []

        for table in classified_report.tables:
            metadata = metadata_lookup.get(table.table_name, {})

            # check metadata violations for this table
            metadata_violations = await self._check_metadata(
                table, metadata, frameworks
            )
            all_violations.extend(metadata_violations)

            # check each PII column for violations
            pii_columns = [
                col for col in table.classified_columns
                if col.classification == Classification.PII
            ]
            for column in pii_columns:
                column_violations = await self._check_pii_column(
                    column, table.table_name, frameworks
                )
                all_violations.extend(column_violations)

        return ViolationReport(
            source_id=classified_report.source_id,
            violations=all_violations,
            critical_count=sum(1 for v in all_violations if v.severity == Severity.CRITICAL),
            high_count    =sum(1 for v in all_violations if v.severity == Severity.HIGH),
            medium_count  =sum(1 for v in all_violations if v.severity == Severity.MEDIUM),
            checked_at=datetime.now(),
        )

    '''This method will check if there is any violations associated with the metadata'''
    async def _check_metadata(
        self,
        table: ClassifiedTable,
        metadata: dict,
        frameworks: list[str],
    ) -> list[Violation]:

        # retrieve policy chunks about governance metadata requirements
        policy_docs = vector_store.search(
            f"data governance metadata requirements table owner retention policy {' '.join(frameworks)}", k=3
        )
        policy_context = "\n\n".join([
            f"[{doc.metadata.get('source', 'unknown')} — page {doc.metadata.get('page_number', '?')}]\n{doc.page_content}"
            for doc in policy_docs
        ])

        user_prompt = f"""Check this table's governance metadata for compliance violations.

        Table: {table.table_name}
        PII columns: {table.pii_count}
        Quasi-PII columns: {table.quasi_pii_count}
        Frameworks: {', '.join(frameworks)}

        Governance metadata:
        {json.dumps(metadata, indent=2)}

        Relevant policy excerpts:
        {policy_context}

        List all violations found:"""

        raw = await self._call_llm(user_prompt)
        return self._parse_violations(raw, table.table_name)


    '''validate each PII column for policy violations'''
    async def _check_pii_column(
        self,
        column: ClassifiedColumn,
        table_name: str,
        frameworks: list[str],
    ) -> list[Violation]:

        # retrieve policy chunks relevant to this specific PII type
        policy_docs = vector_store.search(
            f"compliance requirements for {column.column_name} PII {column.justification[:80]} {' '.join(frameworks)}", k=3
        )
        policy_context = "\n\n".join([
            f"[{doc.metadata.get('source', 'unknown')} — page {doc.metadata.get('page_number', '?')}]\n{doc.page_content}"
            for doc in policy_docs
        ])

        user_prompt = f"""Check this PII column for compliance violations.

        Table: {table_name}
        Column: {column.column_name}
        Classification: {column.classification.value}
        Justification: {column.justification}
        Frameworks: {', '.join(frameworks)}

        Relevant policy excerpts:
        {policy_context}

        List all violations found:"""

        raw = await self._call_llm(user_prompt)
        return self._parse_violations(raw, table_name)

    
    '''helper func to make an llm call'''
    async def _call_llm(self, user_prompt: str) -> str:
        response = await self.llm.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": POLICY_CHECK_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            options={"temperature": 0.0},
        )
        return response["message"]["content"].strip()

    def _parse_violations(self, raw: str, table_name: str) -> list[Violation]:
        try:
            clean = raw.strip().removeprefix("```json").removesuffix("```").strip()
            items = json.loads(clean)

            if not isinstance(items, list):
                return []

            violations = []
            for item in items:
                violations.append(Violation(
                    violation_id     =str(uuid.uuid4()),
                    severity         =Severity(item["severity"]),
                    rule             =item["rule"],
                    affected_columns =item.get("affected_columns", []),
                    table_name       =table_name,
                    framework        =item.get("framework", "GDPR"),
                ))
            return violations

        except (Exception):
            return []  