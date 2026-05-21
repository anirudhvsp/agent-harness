import os
from dotenv import load_dotenv

load_dotenv()

MODEL         = os.getenv("AGENT_MODEL", "baidu/cobuddy:free")
MAX_TOKENS    = int(os.getenv("AGENT_MAX_TOKENS", "8096"))
MAX_ITERS     = int(os.getenv("AGENT_MAX_ITERATIONS", "10"))
API_KEY       = os.getenv("OPENROUTER_API_KEY", "")
BASE_URL      = "https://openrouter.ai/api/v1"
DB_PATH       = os.getenv("AGENT_DB_PATH", "agent_memory.db")


SYSTEM_PROMPT = """You are a helpful AI agent with access to tools, your name is Catalyst-AI with access to tools.
Think step-by-step. Use tools when needed. When you have enough information,
give a clear final answer without calling any more tools."""
