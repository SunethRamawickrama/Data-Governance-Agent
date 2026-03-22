from mcp.server.fastmcp import FastMCP
from services.db_service.db_factory import execute_query
from services.db_service.crud import serialize_row

db_mcp_server = FastMCP()

'''Tools for db access'''

'''this tool will get all the available databases connected to the system by querying the data registry table.
The agent will use this tool to dynamically discover what database to use in a given audit/prompt'''
@db_mcp_server.tool(
        name="get_all_dbs",
        description="list all the databases connected to the system"
)
def get_all_dbs():
    try:
        result = execute_query(
            db_name="data_registry_data",
            sql=""" SELECT * FROM data_sources
                WHERE source_type = 'postgres' AND status = 'active'
                ORDER BY created_at DESC; """ )
        return {
            "count": result.row_count,
            "databases": [row["source_name"] for row in result.rows]
        }
    except Exception as e:
        return {
            "error": str(e)
        }

@db_mcp_server.tool(
        name = "get_schema",
        description="""Returns column names and types for a given table."""
)
def get_schema(db_name: str, table_name: str) -> dict:
    
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

@db_mcp_server.tool(
        name="get_sample_rows",
        description=  """Returns n number of sample rows from a table."""
)
def sample_rows(db_name: str, table_name: str, n: int = 10) -> dict:
  
    result = execute_query(
        db_name,
        f"SELECT * FROM {table_name} LIMIT %s",
        params=(n,)
    )
    return {"rows": result.rows, "row_count": result.row_count}

@db_mcp_server.tool(
        name="list_tables",
        description= """Lists all tables in a database."""
)
def list_tables(db_name: str) -> dict:
   
    result = execute_query(
        db_name,
        """
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = 'public'
        """
    )
    return {"tables": result.rows}

@db_mcp_server.tool(
        name="get_column_stats",
        description="""Returns null count, distinct count, sample values for a column."""
)
def get_column_stats(db_name: str, table_name: str, column_name: str) -> dict:
    
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

@db_mcp_server.tool(
    name="get_table_metadata",
    description="Returns governance metadata for a table: owner, retention policy, access controls."
)
def get_table_metadata(db_name: str, table_name: str) -> dict:
    # query your data_registry or a governance_metadata table
    # for now, return a structured empty shell so downstream nodes 
    # can detect missing metadata as a policy violation
    result = execute_query(
        db_name,
        """
        SELECT *
        FROM information_schema.tables
        WHERE table_name = %s AND table_schema = 'public'
        """,
        params=(table_name,)
    )
    return {
        "owner": None,
        "retention_policy_days": None,
        "encryption_at_rest": None,
        "access_control_list": [],
        "consent_basis": None,
        "table_info": result.rows[0] if result.rows else {}
    }


def main():
    # Initialize and run the server
    db_mcp_server.run(transport="stdio")

if __name__ == "__main__":
    main()