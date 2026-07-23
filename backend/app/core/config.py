import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "NextGen Reads AI"
    
    # Security & JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "7b0d778d91c1b1df4e4e9f3b584ea9c07b0d778d91c1b1df")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    # DB
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./nextgen_reads.db")
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "127.0.0.1")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    
    # LLM Settings (OpenAI / Gemini Mock Switch)
    LLM_MOCK: bool = True
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    class Config:
        case_sensitive = True

settings = Settings()
