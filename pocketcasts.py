import json
import logging
from typing import Any, Dict, Optional

import urllib3

logger = logging.getLogger(__name__)

def do_login(http: urllib3.PoolManager, user: Optional[str], pw: Optional[str]) -> Optional[str]:
    if not user or not pw:
        logger.error("No username or password provided")
        return None

    data = {"email": f"{user}", "password": f"{pw}", "scope": "webplayer"}
    encoded_data = json.dumps(data).encode("utf-8")
    response = http.request(
        "POST",
        "https://api.pocketcasts.com/user/login",
        headers={"Content-Type": "application/json"},
        body=encoded_data,
    )
    
    if response.status != 200:
        error_msg = response.data.decode('utf-8', errors='ignore')
        logger.error("Login failed with status %d: %s", response.status, error_msg)
        raise Exception(f"Login failed with status {response.status}: {error_msg}")
    
    try:
        response_data = json.loads(response.data)
        token = response_data.get("token")
        if not token:
            logger.error("Login response missing token")
            raise Exception("Login response missing token")
        logger.debug("Login successful")
        return token
    except (json.JSONDecodeError, KeyError) as e:
        logger.error("Failed to parse login response: %s", e)
        raise Exception(f"Failed to parse login response: {e}")


def create_auth_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# Documenting the endpoint. This isn't used at all.
def get_history(http: urllib3.PoolManager, token: str) -> Dict[str, Any]:
    header = create_auth_headers(token)
    response = http.request(
        "POST",
        "https://api.pocketcasts.com/user/history",
        headers=header,
    )
    data = json.loads(response.data)
    return data


def search_podcasts(http: urllib3.PoolManager, token: str, term: str) -> Dict[str, Any]:
    logger.debug("Searching for podcasts with term: %s", term)
    header = create_auth_headers(token)
    body = json.dumps({"term":term}, ensure_ascii=False).encode("ascii", errors="ignore")
    header["content-length"] = str(len(body))
    response = http.request(
        "POST",
        "https://api.pocketcasts.com/discover/search",
        headers=header,
        body=body,
    )
    
    if response.status != 200:
        error_msg = response.data.decode('utf-8', errors='ignore')
        logger.error("Search failed with status %d: %s", response.status, error_msg)
        raise Exception(f"Search failed with status {response.status}: {error_msg}")
    
    try:
        return json.loads(response.data)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse search response: %s", e)
        raise Exception(f"Failed to parse search response: {e}")


def search_podcasts_and_get_first_uuid(http: urllib3.PoolManager, token: str, term: str) -> Optional[str]:
    try:
        search_result = search_podcasts(http, token, term)
    except Exception:
        # If search fails, return None so caller can skip this podcast
        return None
    
    try:
        search_result["podcasts"][0]
    except(IndexError, KeyError):
        return None
    # Get the first result
    # It would be very rare to have two podcasts with the same name
    # FIXME: Also check author here. Not sure if authors are consistent
    # across platforms.
    return search_result["podcasts"][0]["uuid"]


def get_subscriptions(http: urllib3.PoolManager, token: str) -> Dict[str, Any]:
    header = create_auth_headers(token)
    body = json.dumps({"v": 1}).encode("utf-8")
    response = http.request(
        "POST",
        "https://api.pocketcasts.com/user/podcast/list",
        headers=header,
        body=body,
    )
    return json.loads(response.data)


def add_subscription(http: urllib3.PoolManager, token: str, uuid: str) -> Optional[Dict[str, Any]]:
    header = create_auth_headers(token)
    body = json.dumps({"uuid": uuid}).encode("utf-8")
    response = http.request(
        "POST", "https://api.pocketcasts.com/user/podcast/subscribe", headers=header, body=body
    )
    
    # Accept both 200 (new subscription) and non-200 (already subscribed or error)
    # as the comment in spotify_to_pocketcasts.py indicates we don't care about the status
    try:
        return json.loads(response.data)
    except json.JSONDecodeError:
        # If response isn't JSON, that's okay - might be already subscribed
        return None


def get_episodes(http: urllib3.PoolManager, token: str, podcast_uuid: str) -> Dict[str, str]:
    header = create_auth_headers(token)
    response = http.request(
        "GET", f"https://podcast-api.pocketcasts.com/podcast/full/{podcast_uuid}", 
        headers=header
    )
    
    if response.status != 200:
        error_msg = response.data.decode('utf-8', errors='ignore')
        logger.error("Get episodes failed with status %d: %s", response.status, error_msg)
        raise Exception(f"Get episodes failed with status {response.status}: {error_msg}")
    
    try:
        data = json.loads(response.data)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse episodes response: %s", e)
        raise Exception(f"Failed to parse episodes response: {e}")
    
    try:
        data["podcast"]["episodes"]
    except(IndexError, KeyError):
        logger.warning("No episodes found in response for podcast UUID: %s", podcast_uuid)
        return {}

    episodes = {}
    for episode in data["podcast"]["episodes"]:
        episodes[episode["title"]] = episode["uuid"]
    logger.debug("Retrieved %d episodes for podcast UUID: %s", len(episodes), podcast_uuid)
    return episodes

def update_podcast_episode(http: urllib3.PoolManager, token: str, body: bytes) -> Dict[str, Any]:
    header = create_auth_headers(token)
    response = http.request(
        "POST", "https://api.pocketcasts.com/sync/update_episode", headers=header, body=body
    )
    
    if response.status != 200:
        error_msg = response.data.decode('utf-8', errors='ignore')
        logger.error("Update episode failed with status %d: %s", response.status, error_msg)
        raise Exception(f"Update episode failed with status {response.status}: {error_msg}")
    
    try:
        return json.loads(response.data)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse update episode response: %s", e)
        raise Exception(f"Failed to parse update episode response: {e}")


if __name__ == "__main__":
    http = urllib3.PoolManager()
    # Note: do_login requires user and pw arguments
    # This is just for testing - should not be run directly
    logger.warning("This module should not be run directly. Use spotify_to_pocketcasts.py instead.")
