from mcp.server.fastmcp import FastMCP
from pathlib import Path
import traceback
from services.db_service.db_factory import execute_query

mcp = FastMCP()

'''Tools for db access'''

'''this tool will get all the available databases connected to the system by querying the data registry table.
The agent will use this tool to dynamically discover what database to use in a given audit/prompt'''
@mcp.tool()
def get_all_dbs():
    try:
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

@mcp.tool()
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

@mcp.tool()
def sample_rows(db_name: str, table_name: str, n: int = 10) -> dict:
    """Returns n sample rows from a table."""
    result = execute_query(
        db_name,
        f"SELECT * FROM {table_name} LIMIT %s",
        params=(n,)
    )
    return {"rows": result.rows, "row_count": result.row_count}

@mcp.tool()
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

@mcp.tool()
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


'''Tools for file access'''
# the agent is only allowed to access files in this root
SANDBOX_ROOT = Path(__file__).resolve().parent.parent
# directories for the agent to ignore
IGNORE_DIRS = {}
# files for the agent to ignore
IGNORE_FILES = {}

@mcp.tool(
        name="read_file",
        description="read a file and return its content"
)
async def read_file(filename):

    file_path = (SANDBOX_ROOT / Path(filename)).resolve()

    try:
        with open(file=file_path, mode="r") as file:
            return file.read()
        
    except Exception as e:
        return f"Error reading file: {str(e)}"
    
@mcp.tool(
        name="list_files",
        description="list file for the given depth in the SANDBOX root"
)
def list_files(
    dir = "",
    max_depth: int = 3
):
    
    try:
        max_depth = int(max_depth)
    except TypeError:
        return "Max depth has to be of type 'int'"
    # c:users/.../copilot/.
    rel_path = (SANDBOX_ROOT / dir).resolve()
    
    tree = ""

    if not rel_path.exists():
        return "Path does not exists"
    if not str(rel_path).startswith(str(SANDBOX_ROOT)):
        return "Access denied"
    
    def build_file_tree(file_path: Path, max_depth=max_depth, indent=""):
        '''c:users/.../copilot , 3, ""
           c:users/.../copilot/agent , 2, ""'''
        nonlocal tree

        if max_depth < 0:
            return 
        
        try:
            for item in sorted(file_path.iterdir(), key=lambda p: (not p.is_dir(), p.name)):

                if item.name in IGNORE_DIRS or item.name in IGNORE_FILES:
                    continue
            
                '''
                agent/ (3)
                    agent/agent.py (2)
                    agent/execution_agent/
                        agent/execution_agent/execution_agent.py (1)
                        agent/execution_agent/utils
                            agent/execution_agent/utils/utils.py (0)
                mcp/
                    mcp/mcp_client.py
                    mcp/mcp_server.py
                other_folders...
                '''
                prefix = str(item.resolve()).removeprefix(str(SANDBOX_ROOT))
                tree += f"{indent}{prefix}\n"

                if item.is_dir():

                    file_path = item.resolve()
                    build_file_tree(file_path, max_depth - 1, indent + "    ")
        except Exception as e:
            traceback.print_exc
            return f"Exception has occured: {str(e)}"

    build_file_tree(rel_path)
    return tree

def main():
    # Initialize and run the server
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()