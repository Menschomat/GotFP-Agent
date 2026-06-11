"""HTTP client helpers for the game API."""

import requests

from .config import API_KEY, BASE_URL


def _headers() -> dict[str, str]:
    """Build authorization headers for API requests."""
    if not API_KEY:
        raise ValueError(
            "GAME_API_KEY environment variable is not set. "
            "Please set it in your .env file."
        )
    return {
        "Authorization": f"ApiKey {API_KEY}",
        "Content-Type": "application/json",
    }


def check_response(response: requests.Response) -> dict | None:
    """Parse detailed error messages from the server on failures.

    Returns an error dict if the response is not 200, or None on success.
    """
    if response.status_code != 200:
        try:
            err_data = response.json()
            err_msg = (
                err_data.get("message")
                or err_data.get("detail")
                or response.text
            )
            return {
                "status": "error",
                "message": f"Server error ({response.status_code}): {err_msg}",
            }
        except Exception:
            return {
                "status": "error",
                "message": f"Server error ({response.status_code}): {response.text}",
            }
    return None


def api_get(path: str) -> dict:
    """Perform a GET request to the game API.

    Args:
        path: API path (e.g. "/game/levels").

    Returns:
        Parsed JSON response dict, or an error dict on failure.
    """
    try:
        response = requests.get(f"{BASE_URL}{path}", headers=_headers())
        err = check_response(response)
        if err:
            return err
        return {"status": "success", "data": response.json()}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def api_post(path: str, payload: dict) -> dict:
    """Perform a POST request to the game API.

    Args:
        path: API path (e.g. "/game/start").
        payload: JSON body to send.

    Returns:
        Parsed JSON response dict, or an error dict on failure.
    """
    try:
        response = requests.post(
            f"{BASE_URL}{path}", json=payload, headers=_headers()
        )
        err = check_response(response)
        if err:
            return err
        return {"status": "success", "data": response.json()}
    except Exception as e:
        return {"status": "error", "message": str(e)}
