import argparse
import json
import logging
import os
from typing import Any

import urllib3
from dotenv import load_dotenv

import pocketcasts
import spotify

logger = logging.getLogger(__name__)
load_dotenv()


def setup_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spotify_to_pocketcasts.py",
        description="Transfer subscriptions and listening history from Spotify to Pocket Casts",
    )
    parser.add_argument(
        "--pocketcasts_user", default=os.environ.get("POCKETCASTS_EMAIL", None)
    )
    parser.add_argument(
        "--pocketcasts_pw", default=os.environ.get("POCKETCASTS_PW", None)
    )
    parser.add_argument(
        "--pocketcasts_token",
        default=os.environ.get("POCKETCASTS_TOKEN", None),
        help="Auth token for pocket casts. Overrides email and password",
    )
    parser.add_argument(
        "--spotify_client_id", default=os.environ.get("SPOTIPY_CLIENT_ID", None)
    )
    parser.add_argument(
        "--spotify_secret", default=os.environ.get("SPOTIPY_CLIENT_SECRET", None)
    )
    parser.add_argument(
        "--spotify_redirect_uri", default=os.environ.get("SPOTIPY_REDIRECT_URI", None)
    )
    return parser


def check_pocketcasts_login_info(
    user: str | None, pw: str | None, token: str | None
) -> bool:
    if token:
        return True

    if not user:
        logger.error(
            "No Pocket Casts username given! Please set POCKETCASTS_EMAIL or use the --pocketcasts_user option"
        )
        return False
    if not pw:
        logger.error(
            "No Pocket Casts password given! Please set POCKETCASTS_PW or use the --pocketcasts_pw option"
        )
        return False
    return True


def check_spotify_secrets_info(
    client_id: str | None, secret: str | None, redirect_uri: str | None
) -> bool:
    if not client_id:
        logger.error(
            "No Spotify Client ID given! Please set SPOTIPY_CLIENT_ID or use the --spotify_client_id option"
        )
        return False
    if not secret:
        logger.error(
            "No Spotify Secret given! Please set SPOTIPY_CLIENT_SECRET or use the --spotify_secret option"
        )
        return False
    if not redirect_uri:
        logger.error(
            "No Spotify Redirect URI given! Please set SPOTIPY_REDIRECT_URI or use the --spotify_redirect_uri option"
        )
        return False
    return True


def create_body_from_spotify_episode(
    spotify_episode: spotify.Episode, uuid: str, episode_uuid: str
) -> bytes:
    MS_TO_S_FACTOR = 1000
    body: dict[str, Any] = {
        "uuid": episode_uuid,
        "podcast": uuid,
    }
    if not spotify_episode.fully_played:
        if spotify_episode.resume_pos_ms > 0:
            body["status"] = 2
            body["position"] = int(spotify_episode.resume_pos_ms / MS_TO_S_FACTOR)
        else:
            body["status"] = 1
    else:
        body["status"] = 3
    return json.dumps(body).encode("utf-8")


def main() -> None:
    parser: argparse.ArgumentParser = setup_arg_parser()
    args = parser.parse_args()

    valid_spotify_args = check_spotify_secrets_info(
        args.spotify_client_id, args.spotify_secret, args.spotify_redirect_uri
    )
    if not valid_spotify_args:
        exit(1)
    spotify_client = spotify.do_login(
        args.spotify_client_id, args.spotify_secret, args.spotify_redirect_uri
    )

    http = urllib3.PoolManager()
    valid_pocketcasts_login = check_pocketcasts_login_info(
        args.pocketcasts_user, args.pocketcasts_pw, args.pocketcasts_token
    )
    if not valid_pocketcasts_login:
        exit(1)

    if args.pocketcasts_token:
        token = args.pocketcasts_token
    else:
        try:
            token = pocketcasts.do_login(
                http, args.pocketcasts_user, args.pocketcasts_pw
            )
            if not token:
                logger.error(
                    "Failed to login to Pocket Casts. Please check your credentials."
                )
                exit(1)
        except Exception as e:
            logger.error("Failed to login to Pocket Casts: %s", e)
            exit(1)

    logger.info("Logged In!")

    podcasts: list[spotify.Show] = spotify.get_podcasts_with_less_info(spotify_client)
    logger.info("Got podcast subscriptions from Spotify.")

    for podcast in podcasts:
        logger.info("Processing %s", podcast.title)
        podcast.episodes = spotify.get_listened_episodes_for_show(
            spotify_client, podcast
        )
        logger.info(
            "%s: Syncing %d episodes from Spotify to Pocketcasts",
            podcast.title,
            len(podcast.episodes),
        )
        uuid = pocketcasts.search_podcasts_and_get_first_uuid(
            http, token, podcast.title
        )
        if uuid is None:
            logger.warning(
                "Could not find podcast '%s' in Pocket Casts. Skipping...",
                podcast.title,
            )
            continue

        # Subscribe to the podcast not caring if it's already subscribed
        # The request will return a non-200 code but we don't care.
        try:
            pocketcasts.add_subscription(http, token, uuid)
        except Exception as e:
            logger.warning(
                "Failed to subscribe to '%s': %s. Continuing anyway...",
                podcast.title,
                e,
            )

        try:
            episodes = pocketcasts.get_episodes(http, token, uuid)
        except Exception as e:
            logger.error(
                "Failed to get episodes for '%s': %s. Skipping this podcast.",
                podcast.title,
                e,
            )
            continue

        for episode in podcast.episodes:
            pocketcasts_episode_uuid = episodes.get(episode.name, None)
            if pocketcasts_episode_uuid is None:
                logger.warning("Failed to sync: %s, %s", podcast.title, episode.name)
                continue
            body = create_body_from_spotify_episode(
                episode, uuid=uuid, episode_uuid=pocketcasts_episode_uuid
            )
            try:
                pocketcasts.update_podcast_episode(http, token, body)
            except Exception as e:
                logger.warning(
                    "Failed to update episode '%s' for '%s': %s",
                    episode.name,
                    podcast.title,
                    e,
                )
                continue


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    main()
