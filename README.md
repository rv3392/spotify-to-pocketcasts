# spotify-to-pocketcasts

This is a script to transfer Spotify podcast subscriptions and listening
history to Pocket Casts.

It uses the openly available Spotify API through the spotipy
module as well as a reverse-engineered Pocket Casts API. So far, I've only tested it for my own switch from Spotify to Pocketcasts for which it worked fairly well.

## Features
- Transfer subscriptions
- Transfer listening history (including marking as played on Pocket Casts)
- Optional script to delete subscriptions from Spotify

## Drawbacks

Before you start using this script please read the drawbacks as there
are some fairly large failure cases where the script does not work 100%. 
The summary is that:

1. Sometimes there are 2+ podcasts with the same name and in those cases
syncing may not work correctly. You could end up subscribed to the wrong podcast
so to mitigate this you should verify your subscriptions after the transfer, and
manually fix any errors.
2. Sometimes the name of episodes is mismatched between Spotify and Pocketcasts.
In such cases the episode with the mismatched name will not have its listening
history synced.
3. The login to Pocketcasts only works for a standard manual email/password login,
not for a google or apple account login.

## How to Use

### Prerequisites
- Python >= 3.13
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

**Using uv (recommended):**
```bash
uv sync
```

**Using pip:**
```bash
pip install -r requirements.txt
```

### Setup

1. Login and add a new application at https://developer.spotify.com/dashboard. Enter whatever you'd like for the app name, app description, and redirect uri. For "Which API/SDKs are you planning to use?", check the Web API box.
   - Export the client ID, client secret and redirect URI as suggested here: https://spotipy.readthedocs.io/en/2.22.0/#quick-start

2. Set the environment variables `POCKETCASTS_EMAIL` and `POCKETCASTS_PW` for your Pocketcasts username and password respectively. For Google or Apple SSO, use `POCKETCASTS_TOKEN` instead, which can be found by logging in via your browser and retrieving the `accessToken` from local storage.
   
   Alternatively, you can create a `.env` file in the project root:
   ```bash
   POCKETCASTS_EMAIL=your.email@email.com
   POCKETCASTS_PW=your_password
   SPOTIPY_CLIENT_ID=your_client_id
   SPOTIPY_CLIENT_SECRET=your_client_secret
   SPOTIPY_REDIRECT_URI=your_redirect_uri
   ```
   
   Or set them manually:
   - Windows: Use `set POCKETCASTS_EMAIL='your.email@email.com'` and then `set POCKETCASTS_PW='your password'`
   - Linux or MacOS: Use `export POCKETCASTS_EMAIL='your.email@email.com'` and then `export POCKETCASTS_PW='your password'`

3. Run the script:
   ```bash
   # Using uv
   uv run spotify_to_pocketcasts.py
   
   # Or using python directly
   python spotify_to_pocketcasts.py
   ```
   
   You'll be asked to authorise the script to read your library and podcast data - this is required to be able to transfer the data.
   You'll also be prompted to copy over the redirect url from your browser a few times. Make sure to copy the full url as shown in
   your browser's address bar with the included code param, not just the base redirect uri you chose earlier.

## Development

### Type Checking
Type checking is available using mypy:
```bash
# Install dev dependencies
uv sync --group dev

# Run type checks
uv run mypy . --ignore-missing-imports
```

### Delete Script
To delete all Spotify podcast subscriptions (use with caution!):
```bash
uv run delete_spotify_subscriptions.py
# or
python delete_spotify_subscriptions.py
```

## Troubleshooting

If you encounter any bugs please open an issue to let me know.

## Future Plans
I welcome any forks and/or open a pull requests for any changes you'd like to make. The main todo just involves making this easier to run by:
- [x] Adding CLI options for passwords/usernames/secrets
- [x] Proper logging instead of print statements
- [x] Type hints throughout the codebase
- [ ] Lots of tests
- [ ] Push to pip to make the script easier to install
- [ ] A web-app version of this script if there is demand
