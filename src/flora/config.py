"""Runtime settings for Flora."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
STATIC_DIR = ROOT_DIR / "src" / "static"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2"
    db_path: Path = DATA_DIR / "flora.db"
    max_history_messages: int = 12
    # Cap reply length for faster local generation (tokens).
    num_predict: int = 120
    # Smaller context = faster prompt eval on CPU.
    num_ctx: int = 1024
    keep_alive: str = "60m"
    host: str = "127.0.0.1"
    port: int = 8000


settings = Settings()
