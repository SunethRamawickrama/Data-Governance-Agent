from mcp_connection.servers import db_server
from agents.agent_interface import AgentInterface
from typing import override
import json

class DatabaseAgent(AgentInterface):
    def __init__(self, tool_executor):
        super().__init__(tool_executor)

    @override
    async def run(self, message_history, user_message=None):
        print("invoking agent\n")

        SYSTEM_PROMPT = f"""
            You are a database scanning agent for a data governance system.

            You have the following tools to inspect and perform actions on databases: {self.tool_executor.groq_tool_schema()}

            When given a task, use your tools to gather the requested information and return
            a structured JSON result. Always be thorough but efficient — only call tools 
            necessary to complete the task.

            Always return your final answer as a JSON object matching the requested schema.
            Never return raw tool output directly.
        
        """
        
        if message_history is None:
            message_history = []
        
        if user_message:
            message_history.append({
                "role": "user",
                "content": user_message
            })

        response = self.groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "system",
                "content": SYSTEM_PROMPT
            }, *message_history],
            tools=self.tool_executor.groq_tool_schema(),
            tool_choice="auto"
        )

        decision = response.choices[0].message

        print(f"groq decision: {decision}\n")

        if decision.tool_calls:
            for tool in decision.tool_calls:

                tool_id = tool.id
                tool_name = tool.function.name
                tool_args = json.loads(tool.function.arguments)

                print(f"Calling tool {tool_name}")

                tool_result = await self.tool_executor.execute_tool(tool_name, tool_args)

                print(f"Tool result {tool_result}")

                message_history.append({
                    "role": "assistant",
                    "tool_calls": [tool]
                })

                message_history.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "name": tool_name,
                    "content": tool_result
                })

            return await self.run(message_history=message_history)

        else:
            message_history.append({
            "role": "assistant",
            "content": decision.content
            })
            return decision.content


