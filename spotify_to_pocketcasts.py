import argparse
import os
from typing import List

import json
import urllib3

import spotify
import pocketcasts


def setup_arg_parser():
    parser = argparse.ArgumentParser(
            prog = "spotify_to_pocketcasts.py",
            description = "Transfer subscriptions and listening history from Spotify to Pocket Casts"
    )
    parser.add_argument("--pocketcasts_user", default=os.environ.get("POCKETCASTS_USER", None))
    parser.add_argument("--pocketcasts_pw", default=os.environ.get("POCKETCASTS_PW", None))
    parser.add_argument("--spotify_client_id", default=os.environ.get("SPOTIFY_CLIENT_ID", None))
    parser.add_argument("--spotify_secret", default=os.environ.get("SPOTIFY_SECRET", None))
    parser.add_argument("--spotify_redirect_uri", default=os.environ.get("SPOTIFY_REDIRECT_URI", None))
    return parser


def check_pocketcasts_login_info(user, pw):
    if not user:
        print("No Pocket Casts username given! Please set POCKETCASTS_USER or use the --pocketcasts_user option")
        return False
    if not pw:
        print("No Pocket Casts password given! Please set POCKETCASTS_PW or use the --pocketcasts_pw option")
        return False
    return True


def check_spotify_secrets_info(client_id, secret, redirect_uri):
    if not client_id:
        print("No Spotify Client ID given! Please set SPOTIFY_CLIENT_ID or use the --spotify_client_id option")
        return False
    if not secret:
        print("No Spotify Secret given! Please set SPOTIFY_SECRET or use the --spotify_secret option")
        return False
    if not redirect_uri:
        print("No Spotify Redirect URI given! Please set SPOTIFY_REDIRECT_URI or use the --spotify_redirect_uri option")
        return False
    return True


def create_body_from_spotify_episode(spotify_episode, uuid, episode_uuid):
    MS_TO_S_FACTOR = 1000
    body = {
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


def main():
    parser: argparse.ArgumentParser = setup_arg_parser()
    args = parser.parse_args()

    valid_args = check_spotify_secrets_info(args.spotify_client_id, args.spotify_secret, args.spotify_redirect_uri)
    if not valid_args:
        exit(1)
    spotify_client = spotify.do_login(args.spotify_client_id, args.spotify_secret, args.spotify_redirect_uri)

    http = urllib3.PoolManager()
    check_pocketcasts_login_info(args.pocketcasts_user, args.pocketcasts_pw)
    if not valid_args:
        exit(1)
    token = pocketcasts.do_login(http, args.pocketcasts_user, args.pocketcasts_pw)

    print("Logged In!")

    podcasts: List[spotify.Show] = spotify.get_podcasts_with_less_info(spotify_client)
    print (f"Got {len(podcasts)} podcast subscriptions from Spotify.")

    for podcast in podcasts:
        log_prefix = f"{podcast.title} by {podcast.publisher}:"
        print(f"{log_prefix} starting processing")
        podcast.episodes = spotify.get_listened_episodes_for_show(spotify_client, podcast, log_prefix)
        print(
            f"{log_prefix} Syncing {len(podcast.episodes)} episodes from Spotify to Pocketcasts"
        )
        uuid = pocketcasts.search_podcasts_and_get_first_uuid(http, token, podcast.title, podcast.publisher, log_prefix)

        print(f"{log_prefix} pocketcasts uuid of this show: {uuid}")

        # Subscribe to the podcast not caring if it's already subscribed
        # The request will return a non-200 code but we don't care.
        pocketcasts.add_subscription(http, token, uuid)
        if uuid == None:
            print(f"{log_prefix} could not find that show on pocketcasts")
            continue

        episodes = pocketcasts.get_episodes(http, token, uuid)

        for episode in podcast.episodes:
            episode_log_prefix = f"{podcast.title} by {podcast.publisher}, episode {episode.name}:"

            pocketcasts_episode_uuid = episodes.get(episode.name, None)
            if pocketcasts_episode_uuid == None:
                print(f"{episode_log_prefix} failed to sync")
                continue

            body = create_body_from_spotify_episode(
                episode, uuid=uuid, episode_uuid=pocketcasts_episode_uuid
            )
            pocketcasts.update_podcast_episode(http, token, body, episode_log_prefix)


if __name__ == "__main__":
    main()
