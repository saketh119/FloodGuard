"""
core/config.py — Pydantic-settings environment configuration.

All values are loaded from the .env file. Import `settings` anywhere in the app.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: str = "development"
    app_port: int = 8000
    debug: bool = True

    # Database
    database_url: str = "sqlite+aiosqlite:///./floodguard.db"

    # IMD Mock / Live
    imd_base_url: str = "http://localhost:8080"

    # Weather (OpenWeatherMap)
    openweather_api_key: str = "dummy"
    openweather_base_url: str = "https://api.openweathermap.org/data/2.5"

    # Scheduler intervals (seconds)
    imd_poll_seconds: int = 300
    weather_poll_seconds: int = 600
    news_poll_seconds: int = 1800

    # OpenRouter
    openrouter_api_key: str = "dummy"


# Singleton — import this everywhere
settings = Settings()
