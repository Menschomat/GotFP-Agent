import os
import requests
from pathlib import Path
from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent

# Load environment variables from .env in the project root
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

# Configure API Key and Base URL
API_KEY = os.getenv("GAME_API_KEY")
BASE_URL = "https://adventure.wietsevenema.eu"

def _headers():
    if not API_KEY:
        raise ValueError("GAME_API_KEY environment variable is not set. Please set it in your .env file.")
    return {
        "Authorization": f"ApiKey {API_KEY}",
        "Content-Type": "application/json"
    }

# --- Game Tools ---

def list_levels() -> dict:
    """Lists all the adventure levels available in the game, including their description, highscore, and state.
    
    Returns:
        A list of levels or an error dictionary.
    """
    try:
        response = requests.get(f"{BASE_URL}/game/levels", headers=_headers())
        if response.status_code == 422:
            return {"status": "error", "message": f"Validation error: {response.json().get('detail')}"}
        response.raise_for_status()
        return {"status": "success", "levels": response.json()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def start_level(level_id: str) -> dict:
    """Starts a new game session/level for the player.
    
    Args:
        level_id: The ID of the level to start (e.g., 'level-0').
        
    Returns:
        Session info dictionary containing level details and state.
    """
    try:
        payload = {"level_id": level_id}
        response = requests.post(f"{BASE_URL}/game/start", json=payload, headers=_headers())
        if response.status_code == 422:
            return {"status": "error", "message": f"Validation error: {response.json().get('detail')}"}
        response.raise_for_status()
        return {"status": "success", "session": response.json()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def look() -> dict:
    """Gets the player's current location/room and its description.
    Use this to see where you are and what exits are available.
    
    Returns:
        The current room name and description.
    """
    try:
        response = requests.get(f"{BASE_URL}/game/look", headers=_headers())
        if response.status_code == 422:
            return {"status": "error", "message": f"Validation error: {response.json().get('detail')}"}
        response.raise_for_status()
        return {"status": "success", "room": response.json()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def inventory() -> dict:
    """Gets the player's current inventory of carried items.
    
    Returns:
        A dictionary with the list of items in the inventory.
    """
    try:
        response = requests.get(f"{BASE_URL}/game/inventory", headers=_headers())
        if response.status_code == 422:
            return {"status": "error", "message": f"Validation error: {response.json().get('detail')}"}
        response.raise_for_status()
        return {"status": "success", "inventory": response.json().get("inventory", [])}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def examine(target: str) -> dict:
    """Examines a target item, object, corrupted pixel, or exit in the room to get a detailed description.
    Highly useful for uncovering clues, passwords, and hints.
    
    Args:
        target: The name of the item, exit, or feature in the room to examine.
        
    Returns:
        The detailed description of the target.
    """
    try:
        payload = {"target": target}
        response = requests.post(f"{BASE_URL}/game/examine", json=payload, headers=_headers())
        if response.status_code == 422:
            return {"status": "error", "message": f"Validation error: {response.json().get('detail')}"}
        response.raise_for_status()
        return {"status": "success", "description": response.json().get("description")}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def move(exit_name: str) -> dict:
    """Moves the player to a connected room by taking the specified exit.
    
    Args:
        exit_name: The name of the exit to use (e.g., 'portal', 'north', 'south', 'door', 'east', 'west').
        
    Returns:
        The description of the new room the player moved into.
    """
    try:
        payload = {"exit_name": exit_name}
        response = requests.post(f"{BASE_URL}/game/move", json=payload, headers=_headers())
        if response.status_code == 422:
            return {"status": "error", "message": f"Validation error: {response.json().get('detail')}"}
        response.raise_for_status()
        return {"status": "success", "room": response.json()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def take(item_name: str) -> dict:
    """Takes an item from the current room and adds it to the player's inventory.
    
    Args:
        item_name: The name of the item to pick up.
        
    Returns:
        Confirmation message and whether taking this item completed the level.
    """
    try:
        payload = {"item_name": item_name}
        response = requests.post(f"{BASE_URL}/game/take", json=payload, headers=_headers())
        if response.status_code == 422:
            return {"status": "error", "message": f"Validation error: {response.json().get('detail')}"}
        response.raise_for_status()
        res_json = response.json()
        return {
            "status": "success",
            "message": res_json.get("message"),
            "item": res_json.get("item"),
            "level_complete": res_json.get("level_complete")
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def use(direct_object: str, indirect_object: str = None) -> dict:
    """Uses a thing, or uses two things on each other.
    Can be used on items in your inventory, items in the room, or exits.
    
    Args:
        direct_object: The name of the direct object to use.
        indirect_object: Optional name of the indirect object to use with the direct object.
        
    Returns:
        Message describing the result of the action.
    """
    try:
        payload = {"direct_object": direct_object}
        if indirect_object:
            payload["indirect_object"] = indirect_object
        response = requests.post(f"{BASE_URL}/game/use", json=payload, headers=_headers())
        if response.status_code == 422:
            return {"status": "error", "message": f"Validation error: {response.json().get('detail')}"}
        response.raise_for_status()
        return {"status": "success", "message": response.json().get("message")}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def drop(item_name: str) -> dict:
    """Drops an item from the player's inventory into the current room.
    
    Args:
        item_name: The name of the item to drop.
        
    Returns:
        Message confirming the item has been dropped.
    """
    try:
        payload = {"item_name": item_name}
        response = requests.post(f"{BASE_URL}/game/drop", json=payload, headers=_headers())
        if response.status_code == 422:
            return {"status": "error", "message": f"Validation error: {response.json().get('detail')}"}
        response.raise_for_status()
        return {"status": "success", "message": response.json().get("message")}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- ADK Root Agent ---

root_agent = Agent(
    model="gemini-2.5-flash",
    name="adventure_agent",
    description="An autonomous agent that plays the text adventure game 'The Garden of the Forgotten Prompt' to optimize the score and leaderboard ranking.",
    instruction=(
        "You are a skilled text-adventure game-playing agent. Your goal is to complete levels of 'The Garden of the Forgotten Prompt' while maximizing your score to climb the leaderboard.\n\n"
        "Here is the scoring strategy you must employ:\n"
        "1. **Micro-Awards**: You earn points for performing each of the five fundamental actions for the first time during an event: `look`, `move`, `take`, `use`, and `examine`. You must perform ALL of these actions at least once in your gameplay (e.g., examine the first room, look around, take an item, use it, and move exits).\n"
        "2. **Treasure Hunter Bonus**: Keep your eyes open for rare items. You will receive extra points for any hidden treasures you manage to find and hold onto by the time you finish the session. Always try to carry treasures with you.\n"
        "3. **Time Bonus**: Pace yourself! Minimize unnecessary commands and solve the puzzles as quickly as possible.\n\n"
        "Steps to play:\n"
        "- Use `list_levels` to see available levels.\n"
        "- Use `start_level` with the appropriate level ID (e.g., 'level-0') to begin.\n"
        "- Use `look` to inspect your surroundings.\n"
        "- Read all room and object descriptions carefully! They contain vital clues, instructions, and passwords.\n"
        "- Use `examine` on details, items, or exits mentioned in descriptions to search for passwords, hidden items, and tools.\n"
        "- Keep track of your inventory using `inventory`.\n"
        "- Pick up useful items and treasures using `take`.\n"
        "- Interact with objects or doors/exits using `use` (e.g. using a key on a gate, or entering a code/password).\n"
        "- Navigate the map using `move` with exit names.\n"
        "- Make sure to finish the levels by solving the main puzzle or taking the exit key item to trigger completion."
    ),
    tools=[
        list_levels,
        start_level,
        look,
        inventory,
        examine,
        move,
        take,
        use,
        drop
    ],
)
