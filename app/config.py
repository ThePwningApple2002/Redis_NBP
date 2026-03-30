from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openrouter_api_key: str
    openai_api_key: str
    redis_url: str = "redis://localhost:6379"
    llm_model: str = "openai/gpt-4o"


settings = Settings()
