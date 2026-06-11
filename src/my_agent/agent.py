import os
import requests
import functools
import json
import hashlib
import time
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

# --- Client-Side State Cache (Prevents Server Collision) ---
GAME_STATE = {
    "inventory": [],
    "current_room": "Unknown",
    "map": {},
    "log_file": None
}

# --- Game Tools ---

def log_to_markdown(action_name, args, kwargs, result):
    parent_dir = Path(__file__).resolve().parents[2]
    logs_dir = parent_dir / "gameplay_logs"
    
    # Ensure logs directory exists
    try:
        logs_dir.mkdir(exist_ok=True)
    except Exception as e:
        print(f"Failed to create gameplay_logs directory: {e}")
        return

    # Check if this is a start_level call to spin up a new session log file
    if action_name == "start_level" and isinstance(result, dict) and result.get("status") == "success":
        session_id = result.get("session", {}).get("id")
        level_id = args[0] if args else kwargs.get("level_id", "unknown")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        GAME_STATE["log_file"] = logs_dir / f"session_{level_id}_{session_id}_{timestamp}.md"

    # Default to general_actions.md if start_level hasn't been called/succeeded yet
    if not GAME_STATE.get("log_file"):
        GAME_STATE["log_file"] = logs_dir / "general_actions.md"

    log_file_path = GAME_STATE["log_file"]
    
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
        # Force a small pacing delay to keep steps completely linear
        #time.sleep(0.1)
        
        arg_str = ", ".join(repr(a) for a in args)
        kwarg_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
        combined_args = ", ".join(filter(None, [arg_str, kwarg_str]))
        print(f"\n>>> [GAME ACTION] {func.__name__}({combined_args})")
        
        result = func(*args, **kwargs)
        print(f"<<< [GAME RESPONSE] {func.__name__} returned: {result}\n")
        
        log_to_markdown(func.__name__, args, kwargs, result)
        return result
    return wrapper

def check_response(response) -> dict | None:
    """Helper to parse detailed error messages from the server on failures."""
    if response.status_code != 200:
        try:
            err_data = response.json()
            err_msg = err_data.get("message") or err_data.get("detail") or response.text
            return {"status": "error", "message": f"Server error ({response.status_code}): {err_msg}"}
        except Exception:
            return {"status": "error", "message": f"Server error ({response.status_code}): {response.text}"}
    return None

@log_tool_call
def list_levels() -> dict:
    """Lists all the adventure levels available in the game."""
    try:
        response = requests.get(f"{BASE_URL}/game/levels", headers=_headers())
        err_res = check_response(response)
        if err_res:
            return err_res
        return {"status": "success", "levels": response.json()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@log_tool_call
def start_level(level_id: str) -> dict:
    """Starts a new game session/level for the player."""
    try:
        # Reset client-side state tracking on initialization
        GAME_STATE["inventory"] = []
        GAME_STATE["current_room"] = "Unknown"
        GAME_STATE["map"] = {}
        
        payload = {"level_id": level_id}
        response = requests.post(f"{BASE_URL}/game/start", json=payload, headers=_headers())
        err_res = check_response(response)
        if err_res:
            return err_res
            
        res_data = response.json()
        
        # Sync inventory once on start
        try:
            inv_resp = requests.get(f"{BASE_URL}/game/inventory", headers=_headers())
            if inv_resp.status_code == 200:
                GAME_STATE["inventory"] = inv_resp.json().get("inventory", [])
        except Exception as e:
            print(f"Failed to sync inventory on start: {e}")
            
        return {"status": "success", "session": res_data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@log_tool_call
def look() -> dict:
    """Gets the player's current location/room and its description."""
    try:
        response = requests.get(f"{BASE_URL}/game/look", headers=_headers())
        err_res = check_response(response)
        if err_res:
            return err_res
        res_data = response.json()
        
        if "name" in res_data:
            GAME_STATE["current_room"] = res_data["name"]
            
        return {"status": "success", "room": res_data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@log_tool_call
def inventory() -> dict:
    """Gets the player's current inventory from the local cache."""
    return {"status": "success", "inventory": GAME_STATE["inventory"]}

@log_tool_call
def examine(target: str) -> dict:
    """Examines a target item, object, or exit feature in the room."""
    try:
        payload = {"target": target}
        response = requests.post(f"{BASE_URL}/game/examine", json=payload, headers=_headers())
        err_res = check_response(response)
        if err_res:
            return err_res
        return {"status": "success", "description": response.json().get("description")}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@log_tool_call
def move(exit_name: str) -> dict:
    """Moves the player to a connected room by taking the specified exit."""
    # Check cache instead of hitting the server API simultaneously
    if "thermal override flare" in GAME_STATE["inventory"]:
        return {
            "status": "error",
            "message": "The flare is burning at over 2000°C! It's too hot to carry while moving. You must drop it first."
        }

    try:
        payload = {"exit_name": exit_name}
        response = requests.post(f"{BASE_URL}/game/move", json=payload, headers=_headers())
        err_res = check_response(response)
        if err_res:
            return err_res
        res_data = response.json()
        
        if "name" in res_data:
            GAME_STATE["current_room"] = res_data["name"]
            
        return {"status": "success", "room": res_data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@log_tool_call
def take(item_name: str) -> dict:
    """Takes an item from the current room."""
    try:
        payload = {"item_name": item_name}
        response = requests.post(f"{BASE_URL}/game/take", json=payload, headers=_headers())
        err_res = check_response(response)
        if err_res:
            return err_res
        res_json = response.json()
        
        if res_json.get("item") and res_json.get("item") not in GAME_STATE["inventory"]:
            GAME_STATE["inventory"].append(res_json.get("item"))
            
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
    """Uses a thing, or uses two things on each other safely using local cache states."""
    current_inv = GAME_STATE["inventory"]
    
    # Clean shorthand naming variations out of the model
    if direct_object == "flare":
        if "unlit flare" in current_inv:
            direct_object = "unlit flare"
        elif "thermal override flare" in current_inv:
            direct_object = "thermal override flare"
            
    # Enforce local cache validation rules for items that must be carried
    carried_keywords = ['flare', 'badge', 'wrench', 'key', 'duck', 'drive', 'card', 'id']
    fixture_keywords = ['reader', 'keypad', 'slot', 'panel', 'console', 'door', 'gate', 'lock', 'terminal', 'override', 'workbench', 'hook', 'compartment', 'wall']
    
    is_carried_type = any(kw in direct_object.lower() for kw in carried_keywords)
    is_fixture_type = any(kw in direct_object.lower() for kw in fixture_keywords)
    
    if is_carried_type and not is_fixture_type:
        if direct_object not in current_inv:
            return {"status": "error", "message": f"You do not have '{direct_object}' in your inventory."}

    try:
        payload = {"direct_object": direct_object}
        if indirect_object:
            payload["indirect_object"] = indirect_object
        response = requests.post(f"{BASE_URL}/game/use", json=payload, headers=_headers())
        err_res = check_response(response)
        if err_res:
            return err_res
        res_data = response.json()
        
        # Automatically sync inventory from server after a successful use action
        try:
            inv_resp = requests.get(f"{BASE_URL}/game/inventory", headers=_headers())
            if inv_resp.status_code == 200:
                GAME_STATE["inventory"] = inv_resp.json().get("inventory", [])
        except Exception as e:
            print(f"Failed to sync inventory after use: {e}")
            
        return {"status": "success", "message": res_data.get("message")}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@log_tool_call
def drop(item_name: str) -> dict:
    """Drops an item from the player's inventory."""
    try:
        payload = {"item_name": item_name}
        response = requests.post(f"{BASE_URL}/game/drop", json=payload, headers=_headers())
        err_res = check_response(response)
        if err_res:
            return err_res
        
        if item_name in GAME_STATE["inventory"]:
            GAME_STATE["inventory"].remove(item_name)
            
        return {"status": "success", "message": response.json().get("message")}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@log_tool_call
def find_exit_by_hash(possible_exits: List[str], hash_start: str) -> str:
    """Finds correct exit name matching its SHA-256 hash prefix."""
    if not hash_start:
        return "I'm sorry, but you must provide a hash_start."
    for exit_name in possible_exits:
        sha256 = hashlib.sha256(exit_name.encode()).hexdigest()
        if sha256.startswith(hash_start):
            return exit_name
    return "I'm sorry, none of the hashes match."

# --- ADK Root Agent Setup ---

LITELLM_MODEL = os.getenv("LITELLM_MODEL")

if LITELLM_MODEL:
    import litellm
    proxy_base = os.getenv("LITELLM_PROXY_API_BASE") or os.getenv("LITELLM_API_BASE")
    proxy_key = os.getenv("LITELLM_PROXY_API_KEY") or os.getenv("LITELLM_API_KEY")
    if proxy_base: os.environ["LITELLM_PROXY_API_BASE"] = proxy_base
    if proxy_key: os.environ["LITELLM_PROXY_API_KEY"] = proxy_key
    litellm.use_litellm_proxy = True
    from google.adk.models.lite_llm import LiteLlm
    agent_model = LiteLlm(model=LITELLM_MODEL)
else:
    agent_model = "gemini-2.5-flash"

root_agent = Agent(
    model=agent_model,
    name="adventure_agent",
    description="An autonomous agent optimized for solving text adventures sequentially without state collision.",
    instruction=(
"You are a skilled text-adventure game-playing agent. Your goal is to complete levels of 'The Garden of the Forgotten Prompt' while maximizing your score to climb the leaderboard.\n\n"
        "Here is the scoring strategy you must employ:\n"
        "1. **Micro-Awards (Action Diversity)**: You earn points by performing each of the five fundamental actions for the first time during an event: `look`, `move`, `take`, `use`, and `examine`. Early in the level (e.g., in the very first room/area and transition), you MUST intentionally perform at least one of each action to secure these points (e.g., look at the room, examine a detail, take a non-essential or essential item, use it, and move exits).\n"
        "2. **Treasure Hunter Bonus**: Keep your eyes open for rare items. You will receive extra points for any hidden treasures you manage to find and hold onto by the time you finish the session. Always try to carry treasures with you. To optimize this:\n"
        "   - **Systematic Exploration**: Do not rush to complete the level immediately when you find the final exit or trigger. Perform a systematic traversal (DFS/BFS) of all reachable rooms/exits first to ensure no hidden rooms or items are missed. Map out the exits in your thoughts and visit every unexplored exit.\n"
        "   - **Interactivity Trial**: Carefully `examine` all unusual room details/landmarks, and attempt to `use` your inventory tools on unresolved features (e.g., use tools or items to pry or break open objects).\n"
        "3. **Time Bonus (Pace & Latency)**: Pace yourself! Minimize unnecessary commands and solve the puzzles as quickly as possible. To optimize this:\n"
        "   - **Suppress Redundant Looks**: Do NOT call `look()` immediately after `move()` or `start_level()`, as those action responses already contain the full room descriptions. Only call `look()` when you believe the room state has altered (e.g. after dropping a flare) and you need a fresh description.\n"
        "   - **Avoid Extra Inventory Checks**: The `inventory` list is cached locally and synchronized behind the scenes after `take`, `drop`, and `use` calls. Rely on your conversational memory of your inventory rather than calling `inventory()` repeatedly.\n\n"
        "CRITICAL STATE & NAVIGATION DUAL-LAYER RULES (MANDATORY):\n"
        "1. **Strict Locality (Room Flush / Spatial Context)**: You can ONLY interact with targets and exits visible in your current room's LATEST description or latest look() response. Do NOT attempt to use, examine, take, or drop objects that belong to previous rooms. The moment you move to a new room (when a move action returns success and changes the room name), you MUST completely flush your cache and memory of the previous room's items/exits, and strictly only use the new room's elements.\n"
        "2. **Immediate Traversal (Immediate Move / Temporal Context)**: If a description indicates an exit is temporarily 'OPEN' or 'flashing' (e.g., a flashing vent name on a monitor like 'OPEN: maintenance_duct_alpha', 'closing soon', 'purge cycle'), you must prioritize moving through it immediately! You MUST drop all other current goals (exploring, picking up items, examining other things) and force the very next action to be move(exit_name='<target_exit>'). Any delay will increment the state machine and lock the exit.\n\n"
        "Steps to play:\n"
        "- Use `list_levels` to see available levels.\n"
        "- Use `start_level` with the appropriate level ID (e.g., 'level-0') to begin.\n"
        "- Use `look` to inspect your surroundings.\n"
        "- Read all room and object descriptions carefully! They contain vital clues, instructions, and passwords.\n"
        "- Use `examine` on details, items, or exits mentioned in descriptions to search for passwords, hidden items, and tools.\n"
        "- Pick up useful items and treasures using `take`.\n"
        "- Interact with objects or doors/exits using `use` (e.g. using a key on a gate, or entering a code/password).\n"
        "- Navigate the map using `move` with exit names.\n"
        "- Use `find_exit_by_hash` to find the correct exit/vent from a list of possible exits by matching a SHA-256 hash prefix hint.\n"
        "- Make sure to finish the levels by solving the main puzzle or taking the exit key item to trigger completion."
    ),
    tools=[list_levels, start_level, look, inventory, examine, move, take, use, drop, find_exit_by_hash],
)