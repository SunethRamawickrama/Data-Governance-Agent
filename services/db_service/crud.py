from services.db_service.db_factory import execute_query
import json
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