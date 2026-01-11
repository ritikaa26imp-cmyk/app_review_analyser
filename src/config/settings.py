import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()


class Settings:
    """Configuration settings loaded from environment variables"""
    
    # Email settings
    GMAIL_USER: str = os.getenv("GMAIL_USER", "")
    GMAIL_APP_PASSWORD: str = os.getenv("GMAIL_APP_PASSWORD", "")
    RECIPIENT_EMAIL: str = os.getenv("RECIPIENT_EMAIL", "")
    
    # LLM settings - Groq API keys for different agents
    # IMPORTANT: All API keys must be set in .env file - never hardcode them here
    GROQ_API_KEY_CLASSIFIER: str = os.getenv("GROQ_API_KEY_CLASSIFIER", "")
    GROQ_API_KEY_STRATEGIST: str = os.getenv("GROQ_API_KEY_STRATEGIST", "")
    GROQ_API_KEY_FALLBACK: str = os.getenv("GROQ_API_KEY_FALLBACK", "")
    
    # Play Store settings
    GROWW_PLAY_STORE_URL: str = os.getenv(
        "GROWW_PLAY_STORE_URL",
        "https://play.google.com/store/apps/details?id=com.nextbillion.groww"
    )
    
    # Date filtering settings
    CUTOFF_DAYS: int = int(os.getenv("CUTOFF_DAYS", "60"))
    CURRENT_DATE: datetime = datetime(2026, 1, 11)  # Hardcoded as per requirements
    CUTOFF_DATE: datetime = CURRENT_DATE - timedelta(days=CUTOFF_DAYS)  # Nov 12, 2025
    
    # Report settings
    MAX_REPORT_WORDS: int = 250


# Singleton instance
settings = Settings()

