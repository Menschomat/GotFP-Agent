"""Gameplay logging — markdown file logger and tool-call decorator."""

import functools
import json
import time
from pathlib import Path

from .config import LOGS_DIR
from .state import game_state


def _format_args(args: tuple, kwargs: dict) -> str:
    """Format function arguments into a human-readable string."""
    arg_str = ", ".join(repr(a) for a in args)
    kwarg_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
    return ", ".join(filter(None, [arg_str, kwarg_str]))


def log_to_markdown(action_name: str, args: tuple, kwargs: dict, result) -> None:
    """Append a game action and its result to the current session markdown log."""
    # Ensure logs directory exists
    try:
        LOGS_DIR.mkdir(exist_ok=True)
    except Exception as e:
        print(f"Failed to create gameplay_logs directory: {e}")
        return

    # Spin up a new session log file on start_level success
    if (
        action_name == "start_level"
        and isinstance(result, dict)
        and result.get("status") == "success"
    ):
        session_id = result.get("session", {}).get("id")
        level_id = args[0] if args else kwargs.get("level_id", "unknown")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        game_state.log_file = LOGS_DIR / f"session_{level_id}_{session_id}_{timestamp}.md"

    # Default to general_actions.md if no session log file yet
    if not game_state.log_file:
        game_state.log_file = LOGS_DIR / "general_actions.md"

    log_file_path = game_state.log_file
    combined_args = _format_args(args, kwargs)

    lines = []
    if action_name == "start_level":
        level_label = args[0] if args else (kwargs.get("level_id") or "New Session")
        lines.append(f"\n# Game Session: {level_label}\n")

    lines.append(f"### `{action_name}({combined_args})`")

    if isinstance(result, (dict, list)):
        try:
            formatted_res = json.dumps(result, indent=2)
            lines.append(f"```json\n{formatted_res}\n```\n")
        except Exception:
            lines.append(f"```text\n{result}\n```\n")
    else:
        lines.append(f"```text\n{result}\n```\n")

    try:
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except Exception as e:
        print(f"Failed to write markdown log: {e}")


def log_tool_call(func):
    """Decorator that logs tool calls to console and markdown."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        combined_args = _format_args(args, kwargs)
        print(f"\n>>> [GAME ACTION] {func.__name__}({combined_args})")

        result = func(*args, **kwargs)
        print(f"<<< [GAME RESPONSE] {func.__name__} returned: {result}\n")

        log_to_markdown(func.__name__, args, kwargs, result)
        return result

    return wrapper
