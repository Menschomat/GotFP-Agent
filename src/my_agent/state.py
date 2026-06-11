"""Client-side game state tracking."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GameState:
    """Tracks client-side game state to prevent redundant server calls."""

    inventory: list[str] = field(default_factory=list)
    current_room: str = "Unknown"
    map: dict = field(default_factory=dict)
    log_file: Path | None = None

    def reset(self) -> None:
        """Reset state for a new game session."""
        self.inventory = []
        self.current_room = "Unknown"
        self.map = {}


# Module-level singleton — shared across all tool functions.
game_state = GameState()
