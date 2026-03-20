from mcp.server.fastmcp import FastMCP
from services.db_service.db_factory import execute_query

db_mcp_server = FastMCP()

'''Tools for db access'''

'''this tool will get all the available databases connected to the system by querying the data registry table.
The agent will use this tool to dynamically discover what database to use in a given audit/prompt'''
@db_mcp_server.tool()
def get_all_dbs():
    try:
        print("Agent decided to get all the dbs in the source registry")
        result = execute_query(
            db_name="data_registry_data",
            sql=""" SELECT * FROM data_sources
                WHERE source_type = 'postgres' AND status = 'active'
                ORDER BY created_at DESC; """ )
        return {
            "count": result.row_count,
            "databases": result.rows
        }
    except Exception as e:
        return {
            "error": str(e)
        }

@db_mcp_server.tool()
def get_schema(db_name: str, table_name: str) -> dict:
    """Returns column names and types for a given table."""
    result = execute_query(
        db_name,
        """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
        """,
        params=(table_name,)
    )
    return {"columns": result.rows}

@db_mcp_server.tool()
def sample_rows(db_name: str, table_name: str, n: int = 10) -> dict:
    """Returns n sample rows from a table."""
    result = execute_query(
        db_name,
        f"SELECT * FROM {table_name} LIMIT %s",
        params=(n,)
    )
    return {"rows": result.rows, "row_count": result.row_count}

@db_mcp_server.tool()
def list_tables(db_name: str) -> dict:
    """Lists all tables in a database."""
    result = execute_query(
        db_name,
        """
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = 'public'
        """
    )
    return {"tables": result.rows}

@db_mcp_server.tool()
def get_column_stats(db_name: str, table_name: str, column_name: str) -> dict:
    """Returns null count, distinct count, sample values for a column."""
    result = execute_query(
        db_name,
        f"""
        SELECT
            COUNT(*) as total_rows,
            COUNT({column_name}) as non_null_rows,
            COUNT(DISTINCT {column_name}) as distinct_values
        FROM {table_name}
        """,
    )
    samples = execute_query(
        db_name,
        f"SELECT DISTINCT {column_name} FROM {table_name} LIMIT 5"
    )
    return {
        "stats": result.rows[0],
        "sample_values": [r[column_name] for r in samples.rows]
    }

def main():
    # Initialize and run the server
    db_mcp_server.run(transport="stdio")

if __name__ == "__main__":
    main()