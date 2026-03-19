class ToolExecutor:
    '''Wrapper class for tool executing to avoid exposing the MCP to the agent'''

    # set of allowed tools shared among class instances
    ALLOWED_TOOLS = {"read_file", "list_files"}
    
    def __init__(self, mcp_client):
        self.mcp_client = mcp_client
        self.tools = {}

    async def list_tools(self):
        response = await self.mcp_client.list_tools()

        # print(response)

        # initialize the tool registry
        for tool in response:
            self.tools[tool.name] = tool

    def groq_tool_schema(self):
        schemas = []
        for tool in self.tools.values():
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                }
            })
        return schemas

    async def execute_tool(self, name, args):
        if name not in self.ALLOWED_TOOLS:
            raise PermissionError("Tool not allowed")
        
        result = await self.mcp_client.call_tool(name, args)
        return result

