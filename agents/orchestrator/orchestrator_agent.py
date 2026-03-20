from typing import override
import json

from agents.agent_interface import AgentInterface

class OrchestratorAgent(AgentInterface):    

    def __init__(self, tool_executor):
        super().__init__(tool_executor)

    @override
    async def run(self, message_history, user_message=None):

        print("invoking agent\n")

        SYSTEM_PROMPT = """You are a data governance orchestrator. You coordinate 
        specialized sub-agents to complete data governance tasks.

        You have access to these agents as tools:
        - database management agent: inspects databases, gets schemas, samples data
        - file management agent: inspects CSV, JSON, Parquet files  
        - field classify agent: classifies columns as PII, Quasi-PII, or SAFE
        - check_policy_violations: checks classified data against GDPR/CCPA rules
        - generate_remediations: proposes fixes for violations

        For any governance task, break it down into steps and delegate to the 
        appropriate sub-agents. Always pass clear, specific task descriptions."""
        
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

