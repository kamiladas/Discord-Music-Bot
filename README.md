
# Discord Music Bot

This is a Discord Music Bot that plays music from YouTube. It allows users to queue, skip, and stop music, and includes interactive controls for ease of use.

## Features

- Play music from YouTube links
- Queue multiple tracks
- Skip the current track
- Stop playback and clear the queue
- Interactive controls via Discord buttons
- Persistent playlist management with a local file

## Requirements

- Python 3.6 or higher
- `discord.py` library
- `pytube` library
- `ytmusicapi` library

## Installation

1. Clone the repository:

```sh
git clone https://github.com/YourUsername/Discord-Music-Bot.git
cd Discord-Music-Bot
```

2. Create a virtual environment and activate it:

```sh
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3. Install the required packages:

```sh
pip install -r requirements.txt
```

4. Set up your Discord bot:

- Go to the [Discord Developer Portal](https://discord.com/developers/applications)
- Create a new application and add a bot to it
- Copy the bot token and replace `YOUR_BOT_TOKEN` in the `Musicbot.py` file with your bot token

## Usage

1. Run the bot:

```sh
python discordbot_test.py
```

2. Invite the bot to your server using the OAuth2 URL generated in the Developer Portal

3. Use the following commands in your Discord server:

- `/p <YouTube URL>`: Play a song or playlist from YouTube
- `/skip`: Skip the current track
- `/stop`: Stop playback and clear the queue
- `/queue`: Display the current queue
- `/menu`: Display interactive controls

## File Structure

- `discordbot_test.py`: Main bot code
- `ytapi.py`: YouTube API helper functions
- `Dockerfile`: Dockerfile for containerizing the bot
- `requirements.txt`: Python dependencies



