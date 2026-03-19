import asyncio
from contextlib import AsyncExitStack
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import traceback

class MCPClient:
    def __init__(self):
        # Initialize session and client objects

        # logger.info("Initializing the MCP client")
        self.session: ClientSession | None = None
        self.exit_stack = AsyncExitStack()

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server
        Args:
            server_script_path: Path to the server script
        """

        # logger.info("server file path: " + server_script_path)

        path = Path(server_script_path).resolve()
        server_params = StdioServerParameters(
            command="uv",
            args=["--directory", str(path.parent), "run", path.name],
            env=None,
        )
      
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        try:
            await self.session.initialize()
        except Exception:
            traceback.print_exc()
    
    async def list_tools(self):
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])
        return tools
    
    async def call_tool(self, name, args):
        result = await self.session.call_tool(name, args)
        return result.content
    
    async def cleanup(self):
        await self.exit_stack.aclose()