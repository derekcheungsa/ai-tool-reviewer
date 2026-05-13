"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./dev.db"

    # Reddit API
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "AI-Tool-Review-Aggregator/1.0"

    # Trustpilot (Lobstr.io)
    lobstr_api_key: str = ""

    # G2 (RapidAPI)
    rapidapi_key: str = ""

    # OpenAI (optional)
    openai_api_key: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
