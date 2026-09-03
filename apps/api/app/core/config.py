"""Environment-driven configuration for the FloodGuard backend."""
import os
from pathlib import Path
from dotenv import load_dotenv

# apps/api/app/core/config.py → API_DIR=apps/api, PROJECT_ROOT=repo root
API_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = API_DIR.parents[1]

load_dotenv(API_DIR / ".env", override=False)


class Settings:
    # --- Upstream sources -------------------------------------------------
    # Points at scripts/mock_imd_server.py today; swap for https://api.imd.gov.in
    # plus an auth header when the real credentials land.
    IMD_BASE_URL: str = os.getenv("IMD_BASE_URL", "http://localhost:8080")
    IMD_TIMEOUT_S: float = float(os.getenv("IMD_TIMEOUT_S", "10"))

    # --- OpenWeather (real live conditions, unlike the IMD mock) ----------
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    OPENWEATHER_BASE_URL: str = os.getenv(
        "OPENWEATHER_BASE_URL", "https://api.openweathermap.org/data/2.5"
    )
    OPENWEATHER_TIMEOUT_S: float = float(os.getenv("OPENWEATHER_TIMEOUT_S", "10"))

    # --- Storage ----------------------------------------------------------
    DB_PATH: Path = Path(os.getenv("DB_PATH", str(API_DIR / "floodguard.db")))
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

    # --- Scheduler --------------------------------------------------------
    COLLECT_INTERVAL_S: int = int(os.getenv("COLLECT_INTERVAL_S", "60"))
    SCHEDULER_ENABLED: bool = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"

    # --- Event correlation ------------------------------------------------
    CORRELATION_WINDOW_HOURS: int = int(os.getenv("CORRELATION_WINDOW_HOURS", "6"))

    # --- ML ---------------------------------------------------------------
    MODEL_DIR: Path = Path(os.getenv("MODEL_DIR", str(PROJECT_ROOT / "services" / "ml" / "models")))
    MODEL_PATH: Path = MODEL_DIR / "flood_severity_hgb.joblib"
    MODEL_METRICS_PATH: Path = MODEL_DIR / "flood_severity_metrics.json"

    # --- RAG --------------------------------------------------------------
    CHROMA_DIR: Path = Path(os.getenv("CHROMA_DIR", str(PROJECT_ROOT / "services" / "rag" / "chroma_db")))
    CHROMA_COLLECTION: str = os.getenv("CHROMA_COLLECTION", "flood_guidelines")
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))

    # --- LLM (Gemini) -----------------------------------------------------
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_BASE_URL: str = os.getenv(
        "GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"
    )

    # --- CORS -------------------------------------------------------------
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")

    @property
    def llm_enabled(self) -> bool:
        return bool(self.GEMINI_API_KEY)

    @property
    def openweather_enabled(self) -> bool:
        return bool(self.OPENWEATHER_API_KEY)


settings = Settings()
