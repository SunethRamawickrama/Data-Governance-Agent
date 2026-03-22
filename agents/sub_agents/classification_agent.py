import json
from datetime import datetime
from ollama import AsyncClient
from services.RAG_service.vector_store import vector_store
from workflow.types import (
    SourceScanReport, ClassifiedReport, ClassifiedTable,
    ClassifiedColumn, Classification
)

CLASSIFICATION_SYSTEM_PROMPT = """You are a data privacy expert specializing in PII classification for compliance audits.

You will be given a column name, its data type, and sample values from a database.
You will also be given relevant policy excerpts from GDPR, CCPA, and other frameworks.

Classify the column as one of:
- PII: Directly identifies a person (name, email, SSN, phone, device ID, IP address)
- QUASI_PII: Identifies a person when combined with other fields (zip code, birth year, gender, timestamp)
- SAFE: No personal identification risk (campaign ID, bid price, product category)

Respond ONLY with a valid JSON object in this exact format:
{
  "classification": "PII" | "QUASI_PII" | "SAFE",
  "justification": "clear explanation citing the policy",
  "policy_refs": ["GDPR Art. 4(1)", "CCPA 1798.140"]
}

No extra text. No markdown. Just the JSON object."""

class ClassificationAgent:

    def __init__(self, model: str = "qwen2.5:7b"):
        self.llm   = AsyncClient()
        self.model = model

    '''get the classification report for the entire db'''
    async def get_classification_report(
        self,
        scan_report: SourceScanReport,
        frameworks: list[str] ) -> ClassifiedReport:
        classified_tables = []

        for table in scan_report.tables:
            classified_columns = await self._classify_table(table, frameworks)

            pii_count       = sum(1 for c in classified_columns if c.classification == Classification.PII)
            quasi_pii_count = sum(1 for c in classified_columns if c.classification == Classification.QUASI_PII)
            safe_count      = sum(1 for c in classified_columns if c.classification == Classification.SAFE)

            classified_tables.append(ClassifiedTable(
                table_name=table.table_name,
                classified_columns=classified_columns,
                metadata=table.metadata,
                pii_count=pii_count,
                quasi_pii_count=quasi_pii_count,
                safe_count=safe_count,
            ))

        return ClassifiedReport(
            source_id=scan_report.source_id,
            frameworks=frameworks,
            tables=classified_tables,
            classified_at=datetime.now(),
        )

    '''get all the classified columns in a table'''
    async def _classify_table(self, table, frameworks: list[str]) -> list[ClassifiedColumn]:
        classified_columns = []
        for column in table.columns:
            classified_column = await self._classify_column(
                column=column,
                table_name=table.table_name,
                frameworks=frameworks,
            )
            classified_columns.append(classified_column)
        return classified_columns
    

    '''classify the given column'''
    async def _classify_column(self, column, table_name: str, frameworks: list[str]) -> ClassifiedColumn:

        # rag search query
        rag_query = (
            f"column named '{column.column_name}' "
            f"with data type '{column.data_type}' "
            f"containing values like {column.sample_values[:3]} "
            f"frameworks: {', '.join(frameworks)}"
        )
        policy_docs = vector_store.search(rag_query, k=4)

        # metadata 
        policy_context = "\n\n".join([
            f"[{doc.metadata.get('source', 'unknown')} — page {doc.metadata.get('page_number', '?')}]\n{doc.page_content}"
            for doc in policy_docs
        ])

        # prompt
        user_prompt = f"""Classify this database column for privacy compliance.

        Table: {table_name}
        Column name: {column.column_name}
        Data type: {column.data_type}
        Sample values: {column.sample_values}
        Frameworks to apply: {', '.join(frameworks)}

        Relevant policy excerpts:
        {policy_context}

        Classify now:"""

        # LLM call
        response = await self.llm.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            options={"temperature": 0.0},
        )

        raw = response["message"]["content"].strip()

        # parse the response
        return self._parse_response(raw, column.column_name)

    def _parse_response(self, raw: str, column_name: str) -> ClassifiedColumn:
        try:
            clean = raw.strip().removeprefix("```json").removesuffix("```").strip()
            data  = json.loads(clean)
            return ClassifiedColumn(
                column_name=column_name,
                classification=Classification(data["classification"]),
                justification=data.get("justification", ""),
                policy_refs=data.get("policy_refs", []),
            )
        except (KeyError, ValueError):
            return ClassifiedColumn(
                column_name=column_name,
                classification=Classification.SAFE,
                justification=f"Parse error — raw response: {raw[:200]}",
                policy_refs=[],
            )

