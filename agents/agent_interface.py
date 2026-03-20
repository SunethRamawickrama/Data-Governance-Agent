from dotenv import load_dotenv
from abc import ABC, abstractmethod
from groq import Groq
import os

class AgentInterface(ABC):

    def __init__(self, tool_executor):
        load_dotenv()
        GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        self.groq_client = Groq(api_key=GROQ_API_KEY)
        self.tool_executor = tool_executor 

    @abstractmethod
    def run(self, message_history, user_message):
        pass