from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class AppSettings(BaseSettings):
    """
    Validates enterprise configuration bounds on application startup.
    Leverages Pydantic type-hint checking for failsafe environment loading.
    """
    # Application settings
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    
    # Infrastructure Database Settings
    DATABASE_URL: str = Field(..., description="Connection string for pgvector instance.")
    
    # Provider Secrets
    OPENAI_API_KEY: str = Field(..., description="Bearer token for OpenAI model endpoints.")
    COHERE_API_KEY: str = Field(..., description="Bearer token for Cohere rerank endpoints.")

    # AI Engine Model Defaults
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    RERANK_MODEL: str = "rerank-v3.5"
    ANSWER_MODEL: str = "gpt-5"
    RAG_DEFAULT_TOP_K: int = Field(default=3, ge=1, le=10)

     # Below this rerank score, no answer is drafted and the question is routed to an SME
    MIN_RERANK_SCORE: float = Field(default=0.40, ge=0.0, le=1.0)

    # Instruct Pydantic to read directly from your local .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore" # Silently ignore extra variables not declared in this class
    )

# Instantiate a single global settings object for your application to import
settings = AppSettings()