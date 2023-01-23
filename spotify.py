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
    episodes: List[Episode] = field(default_factory=list)


RATE_LIMIT = 20


def do_login(client_id, secret, redirect_uri):
    scope = "user-library-read,user-read-playback-position"
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
    return [Show(show["show"]["id"], show["show"]["name"]) for show in shows]


def get_listened_episodes_for_show(sp, show) -> List[Episode]:
    episodes = []
    raw_episodes_json = sp.show_episodes(show.id, limit=50)
    while raw_episodes_json:
        episodes += raw_episodes_json["items"]
        if raw_episodes_json["next"]:
            raw_episodes_json = sp.next(raw_episodes_json)
        else:
            raw_episodes_json = None
    print(f"There are {len(episodes)} episodes!")

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
    print(f"There are {len(listened_episodes)} started episodes!")

    return listened_episodes


def populate_listened_episodes(sp, shows: List[Show]):
    for show in shows:
        print(f"Processing {show.title}")
        show.episodes = get_listened_episodes_for_show(sp, show)
