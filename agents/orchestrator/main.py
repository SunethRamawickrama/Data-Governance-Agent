from agents.orchestrator.orchestrator_agent import OrchestratorAgent
from tools.tool_executor import ToolExecutor
from mcp_connection.mcp_client import MCPClient
import asyncio
import traceback

'''This is the entrance point of the agentic workflow. The orchestrator agent object will recieves a task
and begins its execution here. Inside the agent, it will utlize tools which are subagents to achieve each delegated task'''
async def run(task: str):
    
    try:
        mcp_client = MCPClient()
        await mcp_client.connect_to_server("mcp_connection/servers/main_mcp_server.py")
   
        toolExecutor = ToolExecutor(mcp_client=mcp_client)
        await toolExecutor.list_tools()

        agent = OrchestratorAgent(tool_executor=toolExecutor)
        message_history = []

        agent_result = await agent.run(message_history=message_history, user_message=task) 
        print(agent_result)
            
    except Exception:
        traceback.print_exc()

    finally:
        await mcp_client.cleanup()

if __name__ == "__main__":
     asyncio.run(run("explain all the databases connected to the system"))