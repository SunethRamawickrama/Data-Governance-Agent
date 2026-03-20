from mcp_connection.servers import db_server
from agents.agent_interface import AgentInterface
from typing import override
import json

class DatabaseAgent(AgentInterface):
    def __init__(self, tool_executor):
        super().__init__(tool_executor)

    @override
    async def run(self, message_history, user_message=None, depth:int=0, max_depth:int=10):

        if depth > max_depth:
            return json.dumps({"Error": "Max iterations reached"})
        
        # print("invoking database management agent\n")

        SYSTEM_PROMPT = """
            You are a database scanning agent for a data governance system.

            You MUST follow this exact sequence:

            STEP 1: call get_all_dbs ONCE to get the list of available databases.
            STEP 2: Find the database matching the requested db_name from the results.
            STEP 3: Use the exact name from the results as db_name in ALL subsequent tool calls.
            STEP 4: Only then call list_tables, get_schema, get_sample_rows etc to perform the given task.

            NEVER guess or assume database names — always use the source_name from get_all_dbs.
            DONT'T call get_all_dbs repeatedly if you found the correct database name from a call earlier.
            NEVER repeat a tool call you have already made with the same arguments.
            Once you have sufficient data to answer the task, stop and return JSON.
        
        """
        
        if message_history is None:
            message_history = []
        
        if user_message:
            message_history.append({
                "role": "user",
                "content": user_message
            })

        response = self.ollama_client.chat(
            model="qwen2.5:7b",
            messages=[{
                "role": "system",
                "content": SYSTEM_PROMPT
            }, *message_history],
            tools=self.tool_executor.groq_tool_schema()
        )

        decision = response.message

        # print(f"groq decision: {decision}\n")


        if decision.tool_calls:
            for tool in decision.tool_calls:

                tool_name = tool.function.name
                tool_args = (tool.function.arguments)

                # print(f"Calling tool {tool_name}")

                tool_result = await self.tool_executor.execute_tool(tool_name, tool_args)

                # print(f"Tool result {tool_result}")

                message_history.append({
                    "role": "assistant",
                    "tool_calls": decision.tool_calls
                })

                message_history.append({
                    "role": "tool",
                    "name": tool_name,
                    "content": str(tool_result)
                })

            return await self.run(message_history=message_history, depth=depth+1)

        else:
            message_history.append({
            "role": "assistant",
            "content": decision.content
            })
            return decision.content


