from dotenv import load_dotenv
from abc import ABC, abstractmethod
from groq import Groq
from ollama import Client
import os

class AgentInterface(ABC):

    def __init__(self, tool_executor):
        self.ollama_client = Client()
        self.tool_executor = tool_executor 

    @abstractmethod
    def run(self, message_history, user_message):
        pass