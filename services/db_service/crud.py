from services.db_service.db_factory import execute_query

import json
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

def create_record(db_name: str, table: str, data: dict):
    """
    Generic insert function
    """

    columns = ", ".join(data.keys())
    placeholders = ", ".join(["%s"] * len(data))

    values = []
    for v in data.values():
        if isinstance(v, dict):  # handle JSONB
            values.append(json.dumps(v))
        else:
            values.append(v)

    query = f"""
        INSERT INTO {table} ({columns})
        VALUES ({placeholders})
        RETURNING *;
    """

    return execute_query(db_name=db_name, sql=query, params=values)

def serialize_row(row: dict) -> dict:
    """Convert non-JSON-serializable types to strings"""
    result = {}
    for key, value in row.items():
        if isinstance(value, (datetime, date)):
            result[key] = value.isoformat()
        elif isinstance(value, Decimal):
            result[key] = float(value)
        elif isinstance(value, UUID):
            result[key] = str(value)
        elif isinstance(value, bytes):
            result[key] = value.decode('utf-8', errors='replace')
        elif isinstance(value, str):
            # Ensure string is UTF-8 safe
            result[key] = value.encode('utf-8', errors='replace').decode('utf-8')
        else:
            result[key] = value
    return result