import argparse
import os
from pprint import pprint
from typing import List

import spotify


def setup_arg_parser():
    parser = argparse.ArgumentParser(
        prog="delete_spotify_subscriptions.py",
        description="Delete all podcast subscriptions from Spotify",
    )
    parser.add_argument("--spotify_client_id", default=os.environ.get("SPOTIFY_CLIENT_ID", None))
    parser.add_argument("--spotify_secret", default=os.environ.get("SPOTIFY_SECRET", None))
    parser.add_argument(
        "--spotify_redirect_uri", default=os.environ.get("SPOTIFY_REDIRECT_URI", None)
    )
    return parser


def main():
    parser: argparse.ArgumentParser = setup_arg_parser()
    args = parser.parse_args()

    spotify_client = spotify.do_login(
        args.spotify_client_id, args.spotify_secret, args.spotify_redirect_uri, extra_scope="user-library-modify"
    )
    podcasts: List[spotify.Show] = spotify.get_podcasts_with_less_info(spotify_client)
    print(
        f"\n\nWARNING: THIS WILL DELETE ALL {len(podcasts)} PODCAST SUBSCRIPTIONS FROM SPOTIFY!\n"
    )
    confirm_answer = input("Are you sure you would like to continue [y\\n]:")
    if confirm_answer != "y":
        exit()

    print("\n\nTHIS IS NOT EASILY REVERSIBLE!\n")
    confirm_answer = input("Are you absolutely sure [y\\n]:")
    if confirm_answer != "y":
        exit()
    print("\n")

    deleted_podcasts, response_json = spotify.delete_all_podcast_subscriptions(spotify_client)
    with open("deleted_podcasts.txt", "w") as f:
        for pod in deleted_podcasts:
            f.write(f"{pod.id}: {pod.title}\n")
        if response_json:
            f.write("JSON Response:\n")
            f.write(str(response_json))

    deleted_podcasts_readable = [(pod.id, pod.title) for pod in deleted_podcasts]
    print("The deleted podcasts are. Please take a note of these:")
    pprint(deleted_podcasts_readable)
    print(f"A copy of these deleted podcast subscriptions has also been saved to {f.name}")


if __name__ == "__main__":
    main()
