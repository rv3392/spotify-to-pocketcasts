import logging
from dataclasses import dataclass, field
from typing import Any

import spotipy
from spotipy.oauth2 import SpotifyOAuth

logger = logging.getLogger(__name__)


@dataclass
class Episode:
    name: str
    fully_played: bool
    resume_pos_ms: int


@dataclass
class Show:
    id: str
    title: str
    episodes: list[Episode] = field(default_factory=list)


RATE_LIMIT = 20


def do_login(
    client_id: str, secret: str, redirect_uri: str, extra_scope: str | None = None
) -> spotipy.Spotify:
    scope = "user-library-read,user-read-playback-position"
    if extra_scope:
        scope = scope + "," + extra_scope
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope=scope,
            client_id=client_id,
            client_secret=secret,
            redirect_uri=redirect_uri,
        )
    )
    return sp


def get_podcasts(sp: spotipy.Spotify) -> list[dict[str, Any]]:
    shows = []
    raw_shows_json = sp.current_user_saved_shows(limit=RATE_LIMIT)
    while raw_shows_json:
        shows += raw_shows_json["items"]
        raw_shows_json = sp.next(raw_shows_json) if raw_shows_json["next"] else None
    return shows


def get_podcasts_with_less_info(sp: spotipy.Spotify) -> list[Show]:
    shows = get_podcasts(sp)
    return [Show(show["show"]["id"], show["show"]["name"]) for show in shows]


def get_listened_episodes_for_show(sp: spotipy.Spotify, show: Show) -> list[Episode]:
    episodes = []
    raw_episodes_json = sp.show_episodes(show.id, limit=50)
    while raw_episodes_json:
        episodes += raw_episodes_json["items"]
        if raw_episodes_json["next"]:
            raw_episodes_json = sp.next(raw_episodes_json)
        else:
            raw_episodes_json = None
    logger.debug("Found %d total episodes", len(episodes))

    listened_episodes: list[Episode] = []
    for episode in episodes:
        if episode is not None:
            try:
                listened_episode = Episode(
                    episode["name"],
                    episode["resume_point"].get("fully_played", False),
                    episode["resume_point"].get("resume_position_ms", 0),
                )
                # Ignore episodes that haven't been fully listened to
                # and haven't been started
                if (
                    not listened_episode.fully_played
                    and listened_episode.resume_pos_ms == 0
                ):
                    continue
                listened_episodes.append(listened_episode)
            except KeyError:
                continue
    logger.debug("Found %d started episodes", len(listened_episodes))

    return listened_episodes


def populate_listened_episodes(sp: spotipy.Spotify, shows: list[Show]) -> None:
    for show in shows:
        logger.info("Processing %s", show.title)
        show.episodes = get_listened_episodes_for_show(sp, show)


def delete_all_podcast_subscriptions(
    sp: spotipy.Spotify,
) -> tuple[list[Show], list[Any]]:
    podcasts: list[Show] = get_podcasts_with_less_info(sp)
    podcast_ids = [podcast.id for podcast in podcasts]
    logger.info("Deleting %d podcasts", len(podcast_ids))
    response_jsons: list[Any] = []
    for i in range(0, len(podcast_ids), 20):
        res = sp.current_user_saved_shows_delete(podcast_ids[i : i + 20])
        response_jsons.append(res)
    logger.info("Deleted %d podcasts", len(podcast_ids))
    return (podcasts, response_jsons)
