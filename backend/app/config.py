"""
Configuration management for Vedang backend.
Loads settings from environment variables / .env file.
"""
import os
from dotenv import load_dotenv

# Walk up from app/config.py → backend/ → project root to find .env
_root_env = os.path.join(os.path.dirname(__file__), "../../.env")
if os.path.exists(_root_env):
    load_dotenv(_root_env, override=True)
else:
    load_dotenv(override=True)


class Settings:
    """Central configuration pulled from environment."""

    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "vedang-dev-key")

    # LLM
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai or anthropic
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gpt-4o-mini")

    # File handling
    MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB
    UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "../uploads")
    ALLOWED_EXTENSIONS = {"pdf", "md", "txt", "markdown"}

    # Simulation defaults
    DEFAULT_SIM_ROUNDS = 20
    DEFAULT_AGENTS_PER_ROUND = 5

    def check_required(self):
        """Return list of missing required config keys."""
        problems = []
        if not self.LLM_API_KEY or self.LLM_API_KEY == "your_api_key_here":
            problems.append("LLM_API_KEY is not set")
        return problems
