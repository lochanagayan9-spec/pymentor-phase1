import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Base Directory paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "app" / "static"

# Load environment variables from .env file
load_dotenv(dotenv_path=BASE_DIR / ".env")

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest").strip()
APP_ENV = os.getenv("APP_ENV", "development").strip().lower()

# Multi-Model Fallback Cascade: tested and verified for high availability
# If the primary model encounters a deprecation (404), spike in demand (503), or quota (429),
# PyMentor automatically falls back sequentially to the next candidate model.
MODEL_FALLBACK_CASCADE: List[str] = [
    "gemini-flash-lite-latest",
    "gemini-3-flash-preview",
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-pro-latest",
]

# Server Configuration
HOST = os.getenv("HOST", "127.0.0.1").strip()
PORT = int(os.getenv("PORT", "8000"))

# Memory Configuration (max dialogue turns retained in memory)
MAX_MEMORY_TURNS = int(os.getenv("MAX_MEMORY_TURNS", "10"))

# File Paths
KNOWLEDGE_FILE = DATA_DIR / "knowledge.md"
DATABASE_FILE = DATA_DIR / "pymentor_logs.db"

# Validation Helpers
def is_api_key_valid() -> bool:
    """Check if a genuine Gemini API key is configured."""
    return bool(GEMINI_API_KEY and not GEMINI_API_KEY.startswith("your_") and len(GEMINI_API_KEY) > 10)
