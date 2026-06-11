"""Inventory validation helpers for the `use` tool."""

# Items the player must be carrying to use.
CARRIED_KEYWORDS: list[str] = [
    "flare", "badge", "wrench", "key", "duck", "drive", "card", "id",
]

# Room fixtures — these are used in-place and don't need to be in inventory.
FIXTURE_KEYWORDS: list[str] = [
    "reader", "keypad", "slot", "panel", "console", "door", "gate",
    "lock", "terminal", "override", "workbench", "hook", "compartment", "wall",
]


def resolve_flare_name(direct_object: str, inventory: list[str]) -> str:
    """Normalize shorthand 'flare' to the actual inventory item name."""
    if direct_object == "flare":
        if "unlit flare" in inventory:
            return "unlit flare"
        if "thermal override flare" in inventory:
            return "thermal override flare"
    return direct_object


def validate_use_target(direct_object: str, inventory: list[str]) -> str | None:
    """Check whether the player has the required item in inventory.

    Returns an error message string if validation fails, or None if OK.
    """
    is_carried_type = any(kw in direct_object.lower() for kw in CARRIED_KEYWORDS)
    is_fixture_type = any(kw in direct_object.lower() for kw in FIXTURE_KEYWORDS)

    if is_carried_type and not is_fixture_type:
        if direct_object not in inventory:
            return f"You do not have '{direct_object}' in your inventory."

    return None
