"""Centralized configuration — env vars, constants, and model selection."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env in the project root
_env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=_env_path)

# --- API Configuration ---
API_KEY: str | None = os.getenv("GAME_API_KEY")
BASE_URL: str = "https://adventure.wietsevenema.eu"

# --- Project Paths ---
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
LOGS_DIR: Path = PROJECT_ROOT / "gameplay_logs"


def get_agent_model():
    """Resolve the LLM model to use — LiteLLM proxy or default Gemini."""
    litellm_model = os.getenv("LITELLM_MODEL")

    if litellm_model:
        import litellm
        from google.adk.models.lite_llm import LiteLlm

        proxy_base = os.getenv("LITELLM_PROXY_API_BASE") or os.getenv("LITELLM_API_BASE")
        proxy_key = os.getenv("LITELLM_PROXY_API_KEY") or os.getenv("LITELLM_API_KEY")
        if proxy_base:
            os.environ["LITELLM_PROXY_API_BASE"] = proxy_base
        if proxy_key:
            os.environ["LITELLM_PROXY_API_KEY"] = proxy_key
        litellm.use_litellm_proxy = True
        return LiteLlm(model=litellm_model)

    return "gemini-2.5-flash"
