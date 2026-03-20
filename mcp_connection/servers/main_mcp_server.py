from mcp.server.fastmcp import FastMCP
from agents.sub_agents.db_agent import DatabaseAgent
from mcp_connection.mcp_client import MCPClient
from tools.tool_executor import ToolExecutor
from services.db_service.db_factory import execute_query
from services.db_service.crud import serialize_row
import traceback
import json
import sys

'''This is the main mcp server that the orchestrator agent use.
All the subagents are added as tools for the main agent'''
main_mcp_server = FastMCP()

@main_mcp_server.tool(
        name="get_all_sources",
        description='''Exposes all the sources connected to the system. If a query has an ambigious source name, use this tool
        to get the names of all the databases, files, or buckets connected to the system. Almost always use this tool first to get
        the exact details of a source'''
)
def get_all_sources():
    try:
        result = execute_query(
            db_name="data_registry_data",
            sql=""" SELECT * FROM data_sources
                WHERE status = 'active'
                ORDER BY created_at DESC; """ )
        return {
            "count": result.row_count,
            "databases": [row["source_name"] for row in result.rows]
        }
    except Exception as e:
        return {
            "error": str(e)
        }



@main_mcp_server.tool(
        name = 'database_management_agent',
        description='''Delegates a database inspection task to the DB scanning agent.
                Use this when you need to inspect database tables, get schemas, sample rows,
                check column statistics, or retrieve table metadata. Pass a clear natural
                language description of what information you need.'''
)
async def execute_database_agent(db_name:str, task:str):
    try:
        mcp_client = MCPClient()
        await mcp_client.connect_to_server("mcp_connection/servers/db_server.py")
   
        toolExecutor = ToolExecutor(mcp_client=mcp_client)
        await toolExecutor.list_tools()

        agent = DatabaseAgent(tool_executor=toolExecutor)
        message_history = []

        task = f"""
        Follow the required sequence:
        1. Call get_all_sources to discover available databases
        2. Find the database with name matching: {db_name}
        3. Use its exact source_name for all subsequent calls
        4. Then complete this task: {task}

        Return results as JSON.
        """ 
        agent_result = await agent.run(message_history=message_history, user_message=task) 
        return agent_result
            
    except Exception as e:
        # traceback.print_exc(file=sys.stderr)
        return {"Error": e}

    finally:
        await mcp_client.cleanup()

def main():
    # Initialize and run the server
    main_mcp_server.run(transport="stdio")

if __name__ == "__main__":
    main()