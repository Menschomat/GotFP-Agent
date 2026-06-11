"""Persistent long-term knowledge management for the game agent."""

import json
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
KNOWLEDGE_FILE = KNOWLEDGE_DIR / "game_knowledge.json"


def load_knowledge() -> dict[str, list[str]]:
    """Loads long-term knowledge from the persistent JSON file."""
    if not KNOWLEDGE_FILE.exists():
        return {}
    try:
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load game knowledge: {e}")
        return {}


def save_knowledge(data: dict[str, list[str]]) -> None:
    """Saves long-term knowledge to the persistent JSON file."""
    try:
        KNOWLEDGE_DIR.mkdir(exist_ok=True, parents=True)
        with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Failed to save game knowledge: {e}")


def add_fact(level_id: str, fact: str) -> None:
    """Appends a new fact to the knowledge base of a given level."""
    data = load_knowledge()
    if level_id not in data:
        data[level_id] = []
    
    # Avoid duplicate facts (case-insensitive check)
    fact_stripped = fact.strip()
    if not any(f.lower() == fact_stripped.lower() for f in data[level_id]):
        data[level_id].append(fact_stripped)
        save_knowledge(data)


def get_facts_for_level(level_id: str | None) -> list[str]:
    """Retrieves all facts stored for the given level."""
    if not level_id:
        return []
    data = load_knowledge()
    return data.get(level_id, [])
