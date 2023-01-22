from typing import List

import json
import urllib3

import spotify
import pocketcasts


MS_TO_S_FACTOR = 1000


def create_body_from_spotify_episode(spotify_episode, uuid, episode_uuid):
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
    http = urllib3.PoolManager()

    spotify_client = spotify.do_login()
    token = pocketcasts.do_login(http)
    if not spotify_client or not token:
        print("Failed to login to Spotify and/or Pocketcasts!")
        return
    print("Logged In!")

    podcasts: List[spotify.Show] = spotify.get_podcasts_with_less_info(spotify_client)
    print ("Got podcast subscriptions from Spotify.")

    for podcast in podcasts:
        print(f"Processing {podcast.title}")
        podcast.episodes = spotify.get_listened_episodes_for_show(spotify_client, podcast)
        print(
            f"{podcast.title}: Syncing {len(podcast.episodes)} episodes from Spotify to Pocketcasts"
        )
        uuid = pocketcasts.search_podcasts_and_get_first_uuid(http, token, podcast.title)
        print(uuid)
        # Subscribe to the podcast not caring if it's already subscribed
        # The request will return a non-200 code but we don't care.
        pocketcasts.add_subscription(http, token, uuid)
        episodes = pocketcasts.get_episodes(http, token, uuid)
        for episode in podcast.episodes:
            pocketcasts_episode_uuid = episodes.get(episode.name, None)
            if pocketcasts_episode_uuid == None:
                print(f"Failed to sync: {podcast.title}, {episode.name}")
                continue
            body = create_body_from_spotify_episode(
                episode, uuid=uuid, episode_uuid=pocketcasts_episode_uuid
            )
            pocketcasts.update_podcast_episode(http, token, body)


if __name__ == "__main__":
    main()
