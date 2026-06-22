"""Model layer — LLM configuration and tool binding.

Reads ``.env`` via ``python-dotenv`` and initialises the chat model.
This is a dependency of ``graph`` (the orchestration layer).
"""

import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

from .tools import tools

load_dotenv()

model = init_chat_model(
    os.getenv("BASE_MODEL", "deepseek-chat"),
    model_provider="openai",
    temperature=0,
    base_url=os.getenv("BASE_URL", "https://api.deepseek.com/v1"),
    api_key=os.getenv("API_KEY"),
)

model_with_tools = model.bind_tools(tools)
