"""ADK Root Agent — slim orchestrator that wires config, tools, and prompt."""

from pathlib import Path

from google.adk.agents.llm_agent import Agent

from .config import get_agent_model
from .tools import ALL_TOOLS

# Load the system instruction from the markdown prompt file
_PROMPT_PATH = Path(__file__).parent / "prompts" / "system_instruction.md"
_SYSTEM_INSTRUCTION = _PROMPT_PATH.read_text(encoding="utf-8")

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