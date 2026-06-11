"""Game tool functions exposed to the ADK agent."""

import hashlib
from typing import List

from .api_client import api_get, api_post
from .knowledge import add_fact, get_facts_for_level, load_knowledge, save_knowledge
from .logger import log_tool_call
from .state import game_state
from .validation import resolve_flare_name, validate_use_target


def _inject_room_memory(result: dict) -> dict:
    """Helper to inject persistent knowledge relevant to the current room and level."""
    if result.get("status") == "success" and game_state.level_id:
        room_name = game_state.current_room
        facts = get_facts_for_level(game_state.level_id)
        
        # General level rules/mechanics
        general_facts = [
            f for f in facts 
            if f.lower().startswith("general:") or f.lower().startswith("rule:")
        ]
        
        # Room-specific facts
        room_facts = []
        if room_name and room_name != "Unknown":
            room_facts = [
                f for f in facts 
                if room_name.lower() in f.lower() 
                and not f.lower().startswith("general:") 
                and not f.lower().startswith("rule:")
            ]

        target = result["room"] if "room" in result and isinstance(result["room"], dict) else result
        
        if room_facts:
            target["room_memory"] = room_facts
        if general_facts:
            target["general_knowledge"] = general_facts
            
    return result


@log_tool_call
def list_levels() -> dict:
    """Lists all the adventure levels available in the game."""
    result = api_get("/game/levels")
    if result["status"] == "success":
        return {"status": "success", "levels": result["data"]}
    return result


@log_tool_call
def start_level(level_id: str) -> dict:
    """Starts a new game session/level for the player."""
    game_state.reset()
    game_state.level_id = level_id

    result = api_post("/game/start", {"level_id": level_id})
    if result["status"] != "success":
        return result

    # Sync inventory once on start
    inv_result = api_get("/game/inventory")
    if inv_result["status"] == "success":
        game_state.inventory = inv_result["data"].get("inventory", [])

    # Load and inject persistent knowledge for the level
    facts = get_facts_for_level(level_id)
    ret_data = {"status": "success", "session": result["data"]}
    if facts:
        ret_data["persistent_knowledge"] = facts

    return ret_data


@log_tool_call
def look() -> dict:
    """Gets the player's current location/room and its description."""
    result = api_get("/game/look")
    if result["status"] != "success":
        return result

    room_data = result["data"]
    if "name" in room_data:
        game_state.current_room = room_data["name"]

    ret_data = {"status": "success", "room": room_data}
    return _inject_room_memory(ret_data)


@log_tool_call
def inventory() -> dict:
    """Gets the player's current inventory from the local cache."""
    return {"status": "success", "inventory": game_state.inventory}


@log_tool_call
def examine(target: str) -> dict:
    """Examines a target item, object, or exit feature in the room."""
    result = api_post("/game/examine", {"target": target})
    if result["status"] != "success":
        return result
    return {"status": "success", "description": result["data"].get("description")}


@log_tool_call
def move(exit_name: str) -> dict:
    """Moves the player to a connected room by taking the specified exit."""
    # Check cache — thermal flare must be dropped before moving
    if "thermal override flare" in game_state.inventory:
        return {
            "status": "error",
            "message": (
                "The flare is burning at over 2000°C! "
                "It's too hot to carry while moving. You must drop it first."
            ),
        }

    result = api_post("/game/move", {"exit_name": exit_name})
    if result["status"] != "success":
        return result

    room_data = result["data"]
    if "name" in room_data:
        game_state.current_room = room_data["name"]

    ret_data = {"status": "success", "room": room_data}
    return _inject_room_memory(ret_data)


@log_tool_call
def take(item_name: str) -> dict:
    """Takes an item from the current room."""
    result = api_post("/game/take", {"item_name": item_name})
    if result["status"] != "success":
        return result

    res_data = result["data"]
    item = res_data.get("item")
    if item and item not in game_state.inventory:
        game_state.inventory.append(item)

    return {
        "status": "success",
        "message": res_data.get("message"),
        "item": item,
        "level_complete": res_data.get("level_complete"),
    }


@log_tool_call
def use(direct_object: str, indirect_object: str = None) -> dict:
    """Uses a thing, or uses two things on each other safely using local cache states."""
    current_inv = game_state.inventory

    # Resolve shorthand naming variations
    direct_object = resolve_flare_name(direct_object, current_inv)

    # Enforce local cache validation for items that must be carried
    error_msg = validate_use_target(direct_object, current_inv)
    if error_msg:
        return {"status": "error", "message": error_msg}

    payload = {"direct_object": direct_object}
    if indirect_object:
        payload["indirect_object"] = indirect_object

    result = api_post("/game/use", payload)
    if result["status"] != "success":
        return result

    # Sync inventory from server after a successful use action
    inv_result = api_get("/game/inventory")
    if inv_result["status"] == "success":
        game_state.inventory = inv_result["data"].get("inventory", [])

    return {"status": "success", "message": result["data"].get("message")}


@log_tool_call
def drop(item_name: str) -> dict:
    """Drops an item from the player's inventory."""
    result = api_post("/game/drop", {"item_name": item_name})
    if result["status"] != "success":
        return result

    if item_name in game_state.inventory:
        game_state.inventory.remove(item_name)

    return {"status": "success", "message": result["data"].get("message")}


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


@log_tool_call
def memorize_fact(fact: str) -> dict:
    """Memorizes a fact/rule/password/solution for the current level.

    The fact is saved permanently and shown on subsequent level starts
    and room entry. Make sure to include the room name (e.g. 'Cooling Intake')
    in the fact string if you want it to appear when entering that specific room.
    """
    if not game_state.level_id:
        return {
            "status": "error",
            "message": "No active level session. Start a level first.",
        }
    add_fact(game_state.level_id, fact)
    return {
        "status": "success",
        "message": f"Successfully memorized fact for {game_state.level_id}: '{fact}'",
    }


@log_tool_call
def view_memorized_facts() -> dict:
    """Retrieves all permanently memorized facts for the current level."""
    if not game_state.level_id:
        return {
            "status": "error",
            "message": "No active level session. Start a level first.",
        }
    facts = get_facts_for_level(game_state.level_id)
    return {
        "status": "success",
        "level_id": game_state.level_id,
        "facts": [f"{i}: {f}" for i, f in enumerate(facts)],
    }


@log_tool_call
def forget_fact(fact_index: int) -> dict:
    """Deletes a fact from memory by its index (retrieved from view_memorized_facts)."""
    if not game_state.level_id:
        return {
            "status": "error",
            "message": "No active level session. Start a level first.",
        }
    data = load_knowledge()
    level_facts = data.get(game_state.level_id, [])
    if 0 <= fact_index < len(level_facts):
        removed = level_facts.pop(fact_index)
        data[game_state.level_id] = level_facts
        save_knowledge(data)
        return {
            "status": "success",
            "message": f"Successfully forgot fact: '{removed}'",
        }
    return {
        "status": "error",
        "message": f"Invalid fact index: {fact_index}. Check view_memorized_facts first.",
    }


# Convenient list for agent registration
ALL_TOOLS = [
    list_levels,
    start_level,
    look,
    inventory,
    examine,
    move,
    take,
    use,
    drop,
    find_exit_by_hash,
    memorize_fact,
    view_memorized_facts,
    forget_fact,
]
