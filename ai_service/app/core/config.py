from pydantic_settings import BaseSettings, SettingsConfigDict


from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Pricing Control Tower AI Service"
    app_version: str = "0.1.0"
    environment: str = "local"

    llm_provider: str = "groq"
    llm_model: str = "llama-3.1-8b-instant"
    groq_api_key: str | None = None

    backend_api_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
