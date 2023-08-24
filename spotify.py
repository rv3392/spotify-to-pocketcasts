from dataclasses import dataclass, field
from typing import List

import spotipy
from spotipy.oauth2 import SpotifyOAuth


@dataclass
class Episode:
    name: str
    fully_played: bool
    resume_pos_ms: int


@dataclass
class Show:
    id: str
    title: str
    publisher: str
    episodes: List[Episode] = field(default_factory=list)


RATE_LIMIT = 20


def do_login(client_id, secret, redirect_uri, extra_scope=None):
    scope = "user-library-read,user-read-playback-position"
    if extra_scope:
        scope = scope + "," + extra_scope
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope=scope, client_id=client_id, client_secret=secret, redirect_uri=redirect_uri
        )
    )
    return sp


def get_podcasts(sp):
    shows = []
    raw_shows_json = sp.current_user_saved_shows(limit=RATE_LIMIT)
    while raw_shows_json:
        shows += raw_shows_json["items"]
        if raw_shows_json["next"]:
            raw_shows_json = sp.next(raw_shows_json)
        else:
            raw_shows_json = None
    return shows


def get_podcasts_with_less_info(sp):
    shows = get_podcasts(sp)
    return [Show(show["show"]["id"], show["show"]["name"], show["show"]["publisher"]) for show in shows]


def get_listened_episodes_for_show(sp, show, log_prefix) -> List[Episode]:
    episodes = []
    raw_episodes_json = sp.show_episodes(show.id, limit=50)
    while raw_episodes_json:
        episodes += raw_episodes_json["items"]
        if raw_episodes_json["next"]:
            raw_episodes_json = sp.next(raw_episodes_json)
        else:
            raw_episodes_json = None

    listened_episodes: List[Episode] = []
    for episode in episodes:
        try:
            listened_episode = Episode(
                episode["name"],
                episode["resume_point"].get("fully_played", False),
                episode["resume_point"].get("resume_position_ms", 0),
            )
            # Ignore episodes that haven't been fully listened to and haven't been started
            if not listened_episode.fully_played and listened_episode.resume_pos_ms == 0:
                continue
            listened_episodes.append(listened_episode)
        except (KeyError):
            continue
    print(f"{log_prefix} there are {len(episodes)} episodes on Sporify, which {len(listened_episodes)} are started!")

    return listened_episodes


def populate_listened_episodes(sp, shows: List[Show]):
    for show in shows:
        print(f"Processing {show.title}")
        show.episodes = get_listened_episodes_for_show(sp, show)


def delete_all_podcast_subscriptions(sp: spotipy.Spotify):
    podcasts: List[Show] = get_podcasts_with_less_info(sp)
    podcast_ids = [podcast.id for podcast in podcasts]
    print(f"Deleting {len(podcast_ids)} podcasts!")
    response_jsons = []
    for i in range(0, len(podcast_ids), 20):
        res = sp.current_user_saved_shows_delete(podcast_ids[i:i+20])
        response_jsons.append(res)
    return (podcasts, response_jsons)
