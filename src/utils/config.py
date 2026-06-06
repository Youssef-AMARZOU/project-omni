import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration centralisée via Pydantic Settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    hf_api_token: str = ""
    fallback_llm_provider: str = "anthropic"

    # Databases
    postgres_dsn: str = "postgresql://omni:omni_password@localhost:5432/omni_n8n"
    qdrant_url: str = "http://localhost:6333"
    mongo_url: str = "mongodb://omni:omni_password@localhost:27017/omni_logs?authSource=admin"
    redis_url: str = "redis://localhost:6379/0"

    # RAG
    embedding_model: str = "text-embedding-3-large"
    collection_name: str = "omni_tasks"

    # Resilience
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60

    # Logging
    log_level: str = "INFO"
    omni_data_dir: str = "./data"

    # External integrations
    jira_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    jira_project_key: str = "OMNI"

    notion_token: str = ""
    notion_database_id: str = ""

    github_token: str = ""
    github_repo_owner: str = ""
    github_repo_name: str = ""

    gitlab_token: str = ""
    gitlab_project_id: str = ""
    gitlab_url: str = "https://gitlab.com"

    # Hugging Face
    hf_repo_id: str = ""
    hf_private: bool = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
