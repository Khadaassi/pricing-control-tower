from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Pricing Control Tower AI Service"
    app_version: str = "0.1.0"
    environment: str = "local"

    llm_provider: str = "groq"
    llm_model: str = "llama-3.1-8b-instant"
    groq_api_key: str | None = None

    backend_api_url: str = "http://localhost:8000"

    # RAG — embedding provider
    embedding_provider: str = "ollama"
    embedding_model_name: str = "mxbai-embed-large"
    ollama_base_url: str = "http://localhost:11434"
    embedding_timeout_seconds: float = 120.0

    # RAG — vector store
    chromadb_url: str = "http://localhost:8010"
    rag_collection_name: str = "pricing_control_tower_docs"
    rag_top_k: int = 5
    rag_min_score: float = 0.45
    rag_max_context_chars: int = 6000
    rag_max_displayed_sources: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
