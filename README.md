# spotify-to-pocketcasts

This is a script to transfer Spotify podcast subscriptions and listening
history to Pocketcasts.

It uses the openly available third-party Spotify API through the spotipy
module as well as a reverse-engineered Pocketcasts API. So far, I've only tested it for my own switch from Spotify to Pocketcasts for which it worked fairly well.

## Drawbacks

Before you start using this script please read the drawbacks as there
are some fairly large failure cases where the script does not work 100%. 
The TDLR is that:

1. Sometimes there are 2+ podcasts with the same name and in those cases
syncing may not work correctly. You could end up subscribed to the wrong podcast.
2. Sometimes the name of episodes is mismatched between Spotify and Pocketcasts.
In such cases the episode with the mismatched name will not have its listening
shistory synced.

## How to Use
1. Install Python >= 3.11 and run `pip install -r requirements.txt` to install all Python requirements
2. Setup a new application at https://developer.spotify.com/dashboard. The name
does not matter.
   - Export the client ID, client secret and redirect URI as suggested here: https://spotipy.readthedocs.io/en/2.22.0/#quick-start
3. Set the environment variables POCKETCASTS_EMAIL and POCKETCASTS_PW for your Pocketcasts username and password respectively. 
    - Windows: Use `set POCKETCASTS_EMAIL='your.email@email.com'`
    - Linux or MacOS: Use `export POCKETCASTS_EMAIL='your.email@email.com'`
    - Repeat the same but for `POCKETCASTS_PW`
4. Run the script using 
   ```bsh
   python spotify_to_pocketcasts.py
   ``` 
   You'll be asked to authorise the script to read your library and podcast data - this is required to be able to transfer the data.

If you encounter any bugs please open an issue to let me know.

## Future Plans
I welcome any forks and/or open a pull requests for any changes you'd like to make. The main todo just involves making this easier to run by:
1. Adding CLI options for passwords/usernames/secrets
2. Push to pip to make the script easier to install
