from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5433/sports_market"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]
    sportsdataio_api_key: str | None = None
    sportsdataio_base_url: str = "https://api.sportsdata.io/v3"
    odds_api_key: str | None = None
    odds_api_base_url: str = "https://api.the-odds-api.com/v4"
    do_model_access_key: str | None = None
    do_inference_base_url: str = "https://inference.do-ai.run"
    do_inference_model: str = "openai-gpt-oss-20b"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
