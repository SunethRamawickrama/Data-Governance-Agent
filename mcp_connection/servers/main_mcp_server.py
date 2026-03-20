from mcp.server.fastmcp import FastMCP
from agents.sub_agents.db_agent import DatabaseAgent
from mcp_connection.mcp_client import MCPClient
from tools.tool_executor import ToolExecutor
import traceback

'''This is the main mcp server that the orchestrator agent use.
All the subagents are added as tools for the main agent'''
main_mcp_server = FastMCP()

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

        task = {'database_name': db_name, 'task': task}
        agent_result = await agent.run(message_history=message_history, user_message=task) 
        print(agent_result)
        return agent_result
            
    except Exception:
        traceback.print_exc()

    finally:
        await mcp_client.cleanup()

def main():
    # Initialize and run the server
    main_mcp_server.run(transport="stdio")

if __name__ == "__main__":
    main()