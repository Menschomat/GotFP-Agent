"""ADK Root Agent — slim orchestrator that wires config, tools, and prompt."""

from pathlib import Path

from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.agents.llm_agent import Agent
from google.adk.apps.app import App

from .config import get_agent_model, ON_GCP
from .tools import ALL_TOOLS

# Load the system instruction from the markdown prompt file
_PROMPT_PATH = Path(__file__).parent / "prompts" / "system_instruction.md"
_SYSTEM_INSTRUCTION = _PROMPT_PATH.read_text(encoding="utf-8")

# Dynamically append environment score information based on the ON_GCP flag
if ON_GCP:
    _SYSTEM_INSTRUCTION += (
        "\n\nENVIRONMENT NOTE:\n"
        "You are running directly ON GCP. All scores are at full capacity (100% value)."
    )
else:
    _SYSTEM_INSTRUCTION += (
        "\n\nENVIRONMENT NOTE:\n"
        "You are running in a local/non-GCP environment. All scores here are 5% lower "
        "than what can be achieved on GCP because of a 5% GCP platform bonus. Keep this "
        "in mind if local scores look slightly lower than historical GCP high scores."
    )

root_agent = Agent(
    model=get_agent_model(),
    name="adventure_agent",
    description=(
        "An autonomous agent optimized for solving text adventures "
        "sequentially without state collision."
    ),
    instruction=_SYSTEM_INSTRUCTION,
    tools=ALL_TOOLS,
)

# Enable context caching across all agents in the application
cache_config = ContextCacheConfig(
    cache_intervals=10,
    ttl_seconds=1800,
    min_tokens=0,
)

app = App(
    name="text_adventure_bot",
    root_agent=root_agent,
    context_cache_config=cache_config,
)