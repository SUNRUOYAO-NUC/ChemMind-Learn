import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "sk-your-api-key-here")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
    WEB_PORT: int = int(os.getenv("WEB_PORT", "8000"))


config = Config()