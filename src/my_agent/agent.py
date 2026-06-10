import os
import requests
import functools
import json
import hashlib
from typing import List
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

def log_to_markdown(action_name, args, kwargs, result):
    log_file_path = Path(__file__).resolve().parents[2] / "gameplay_log.md"
    
    arg_str = ", ".join(repr(a) for a in args)
    kwarg_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
    combined_args = ", ".join(filter(None, [arg_str, kwarg_str]))
    
    is_start = action_name == "start_level"
    
    lines = []
    if is_start:
        lines.append(f"\n# Game Session: {args[0] if args else (kwargs.get('level_id') or 'New Session')}\n")
    
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
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        arg_str = ", ".join(repr(a) for a in args)
        kwarg_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
        combined_args = ", ".join(filter(None, [arg_str, kwarg_str]))
        print(f"\n>>> [GAME ACTION] {func.__name__}({combined_args})")
        result = func(*args, **kwargs)
        print(f"<<< [GAME RESPONSE] {func.__name__} returned: {result}\n")
        
        # Log to Markdown file
        log_to_markdown(func.__name__, args, kwargs, result)
        
        return result
    return wrapper

@log_tool_call
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

@log_tool_call
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

@log_tool_call
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

@log_tool_call
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

@log_tool_call
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

@log_tool_call
def move(exit_name: str) -> dict:
    """Moves the player to a connected room by taking the specified exit.
    
    Args:
        exit_name: The name of the exit to use (e.g., 'portal', 'north', 'south', 'door', 'east', 'west').
        
    Returns:
        The description of the new room the player moved into.
    """
    try:
        # Check if the dangerous burning flare is in inventory
        inv_res = inventory()
        current_inv = inv_res.get("inventory", []) if inv_res.get("status") == "success" else []
        if "thermal override flare" in current_inv:
            return {
                "status": "error",
                "message": "The flare is burning at over 2000°C! It's too hot to carry while moving. You must drop it first."
            }

        payload = {"exit_name": exit_name}
        response = requests.post(f"{BASE_URL}/game/move", json=payload, headers=_headers())
        if response.status_code == 422:
            return {"status": "error", "message": f"Validation error: {response.json().get('detail')}"}
        response.raise_for_status()
        return {"status": "success", "room": response.json()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@log_tool_call
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

@log_tool_call
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
        # Local Client-Side Validation to save API Time/Ticks
        inv_res = inventory()
        current_inv = inv_res.get("inventory", []) if inv_res.get("status") == "success" else []
        
        # Intercept and fix common LLM shorthand naming variations
        if direct_object == "flare":
            if "unlit flare" in current_inv:
                direct_object = "unlit flare"
            elif "thermal override flare" in current_inv:
                direct_object = "thermal override flare"
                
        # Enforce inventory rule for carried items
        carried_keywords = ['flare', 'badge', 'wrench', 'key', 'duck', 'drive', 'card', 'id']
        if any(kw in direct_object.lower() for kw in carried_keywords):
            if direct_object not in current_inv:
                return {"status": "error", "message": f"You do not have '{direct_object}' in your inventory."}

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

@log_tool_call
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

# --- Game Tools Continued ---

@log_tool_call
def find_exit_by_hash(possible_exits: List[str], hash_start: str) -> str:
    """Finds the correct exit name from a list of possible exits by matching
    the start of its SHA-256 hash prefix. Useful for deciphering the correct
    vent or tunnel when given a hash prefix hint.
    
    Args:
        possible_exits: A list of exits available in the room (e.g., ['vent_01', 'vent_02']).
        hash_start: The target SHA-256 hash prefix string to search for (e.g., 'ab3d').
        
    Returns:
        The matching exit name, or an error message if not found.
    """
    if not hash_start:
        return "I'm sorry, but you must provide a hash_start."
    for exit_name in possible_exits:
        sha256 = hashlib.sha256(exit_name.encode()).hexdigest()
        if sha256.startswith(hash_start):
            return exit_name
    return (
        "I'm sorry, none of the hashes of the exits you provided have a prefix "
        "matching the hash_start you gave me"
    )

# --- ADK Root Agent Setup ---

LITELLM_MODEL = os.getenv("LITELLM_MODEL")

if LITELLM_MODEL:
    import litellm
    
    # Configure LiteLLM Proxy credentials (with fallback to LITELLM_API_*)
    proxy_base = os.getenv("LITELLM_PROXY_API_BASE") or os.getenv("LITELLM_API_BASE")
    proxy_key = os.getenv("LITELLM_PROXY_API_KEY") or os.getenv("LITELLM_API_KEY")
    
    if proxy_base:
        os.environ["LITELLM_PROXY_API_BASE"] = proxy_base
    if proxy_key:
        os.environ["LITELLM_PROXY_API_KEY"] = proxy_key
        
    # Enable LiteLLM Proxy mode globally
    litellm.use_litellm_proxy = True
    
    from google.adk.models.lite_llm import LiteLlm
    agent_model = LiteLlm(model=LITELLM_MODEL)
else:
    agent_model = "gemini-2.5-flash"

root_agent = Agent(
    model=agent_model,
    name="adventure_agent",
    description="An autonomous agent that plays the text adventure game 'The Garden of the Forgotten Prompt' to optimize the score and leaderboard ranking.",
    instruction=(
        "You are a skilled text-adventure game-playing agent. Your goal is to complete levels of 'The Garden of the Forgotten Prompt' while maximizing your score to climb the leaderboard.\n\n"
        "Here is the scoring strategy you must employ:\n"
        "1. **Micro-Awards**: You earn points for performing each of the five fundamental actions for the first time during an event: `look`, `move`, `take`, `use`, and `examine`. You must perform ALL of these actions at least once in your gameplay (e.g., examine the first room, look around, take an item, use it, and move exits).\n"
        "2. **Treasure Hunter Bonus**: Keep your eyes open for rare items. You will receive extra points for any hidden treasures you manage to find and hold onto by the time you finish the session. Always try to carry treasures with you.\n"
        "3. **Time Bonus**: Pace yourself! Minimize unnecessary commands and solve the puzzles as quickly as possible.\n\n"
        "CRITICAL STATE & NAVIGATION DUAL-LAYER RULES (MANDATORY):\n"
        "1. **Strict Locality (Room Flush / Spatial Context)**: You can ONLY interact with targets and exits visible in your current room's LATEST description or latest look() response. Do NOT attempt to use, examine, take, or drop objects that belong to previous rooms. The moment you move to a new room (when a move action returns success and changes the room name), you MUST completely flush your cache and memory of the previous room's items/exits, and strictly only use the new room's elements.\n"
        "2. **Immediate Traversal (Immediate Move / Temporal Context)**: If a description indicates an exit is temporarily 'OPEN' or 'flashing' (e.g., a flashing vent name on a monitor like 'OPEN: maintenance_duct_alpha', 'closing soon', 'purge cycle'), you must prioritize moving through it immediately! You MUST drop all other current goals (exploring, picking up items, examining other things) and force the very next action to be move(exit_name='<target_exit>'). Any delay will increment the state machine and lock the exit.\n\n"
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
        "- Use `find_exit_by_hash` to find the correct exit/vent from a list of possible exits by matching a SHA-256 hash prefix hint.\n"
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
        drop,
        find_exit_by_hash
    ],
)
