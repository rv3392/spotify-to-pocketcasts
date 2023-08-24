import os

import json
import urllib3

def do_login(http, user, pw):
    if not user or not pw:
        return None

    data = {"email": f"{user}", "password": f"{pw}", "scope": "webplayer"}
    encoded_data = json.dumps(data).encode("utf-8")
    print(encoded_data)
    response = http.request(
        "POST",
        "https://api.pocketcasts.com/user/login",
        headers={"Content-Type": "application/json"},
        body=encoded_data,
    )
    token = json.loads(response.data)["token"]
    print(token)
    return token


def create_auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# Documenting the endpoint. This isn't used at all.
def get_history(http, token):
    header = create_auth_headers(token)
    response = http.request(
        "POST",
        "https://api.pocketcasts.com/user/history",
        headers=header,
    )
    data = json.loads(response.data)
    return data


def search_podcasts(http, token, term, log_prefix):
    header = create_auth_headers(token)
    body = json.dumps({"term":term}, ensure_ascii=False).encode("utf-8", errors="ignore")
    header["content-length"] = len(body)
    print(f"{log_prefix} searching podcasts in pocketcasts; header: {header}, body: {body}")
    response = http.request(
        "POST",
        "https://api.pocketcasts.com/discover/search",
        headers=header,
        body=body,
    )
    return json.loads(response.data)


def search_podcasts_and_get_first_uuid(http, token, term, publisher, log_prefix):
    search_result = search_podcasts(http, token, term, log_prefix)
    try:
        search_result["podcasts"][0]
    except(IndexError, KeyError):
        return None

    if len(search_result["podcasts"]) > 1 and search_result["podcasts"][0]["title"] != term:
        search_result_podcast = [x for x in search_result["podcasts"] if x["author"] == publisher]

        if len(search_result_podcast) == 1:
            return search_result_podcast
        else:
            return None


    return search_result["podcasts"][0]["uuid"]


def get_subscriptions(http, token):
    header = create_auth_headers(token)
    body = json.dumps({"v": 1}).encode("utf-8")
    response = http.request(
        "POST",
        "https://api.pocketcasts.com/user/podcast/list",
        headers=header,
        body=body,
    )
    return json.loads(response.data)


def add_subscription(http, token, uuid):
    header = create_auth_headers(token)
    body = json.dumps({"uuid": uuid}).encode("utf-8")
    response = http.request(
        "POST", "https://api.pocketcasts.com/user/podcast/subscribe", headers=header, body=body
    )
    return json.loads(response.data)


def get_episodes(http, token, podcast_uuid):
    header = create_auth_headers(token)
    response = http.request(
        "GET", f"https://podcast-api.pocketcasts.com/podcast/full/{podcast_uuid}",
        headers=header
    )
    data = json.loads(response.data)
    try:
        data["podcast"]["episodes"]
    except(IndexError, KeyError):
        return {}

    episodes = {}
    for episode in data["podcast"]["episodes"]:
        episodes[episode["title"]] = episode["uuid"]
    return episodes

def update_podcast_episode(http, token, body, log_prefix):
    print(f"{log_prefix} Updating episode - {body}")

    header = create_auth_headers(token)
    response = http.request(
        "POST", "https://api.pocketcasts.com/sync/update_episode", headers=header, body=body
    )
    return json.loads(response.data)


if __name__ == "__main__":
    http = urllib3.PoolManager()
    token = do_login(http)
    history = get_history(http, token)
    print(history)
