# Bocchi

A Discord music bot that plays music from **YouTube** and **Spotify**, built with Python.

## Features

- **YouTube playback** — Play songs and playlists from YouTube URLs or search queries
- **Spotify support** — Play tracks, albums, and playlists from Spotify links (resolved via YouTube)
- **Queue management** — Full queue with skip, shuffle, remove, and loop controls
- **Slash commands** — Modern Discord slash command interface
- **Rich embeds** — Beautiful now-playing and queue displays

## Commands

| Command | Description |
|---------|-------------|
| `/play <query>` | Play a song from YouTube/Spotify URL or search query |
| `/skip` | Skip the current song |
| `/pause` | Pause playback |
| `/resume` | Resume playback |
| `/stop` | Stop playback and clear the queue |
| `/queue` | Show the current queue |
| `/nowplaying` | Show the currently playing song |
| `/loop` | Toggle loop for the current song |
| `/shuffle` | Shuffle the queue |
| `/remove <position>` | Remove a song from the queue by position |
| `/disconnect` | Disconnect the bot from the voice channel |

## Prerequisites

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/) installed and available in PATH
- A [Discord Bot Token](https://discord.com/developers/applications)
- (Optional) [Spotify API credentials](https://developer.spotify.com/dashboard) for Spotify link support

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/SirWilli2m/discord-music-bot.git
cd discord-music-bot
```

### 2. Install dependencies

```bash
pip install .
```

### 3. Install FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
DISCORD_TOKEN=your-discord-bot-token-here
SPOTIFY_CLIENT_ID=your-spotify-client-id-here
SPOTIFY_CLIENT_SECRET=your-spotify-client-secret-here
```

### 5. Run the bot

```bash
python run.py
```

## Docker

Make sure you have a `.env` file with your credentials (see step 4 above).

### Using Docker Compose (recommended)

```bash
docker compose up -d
```

To stop the bot:

```bash
docker compose down
```

To rebuild after code changes:

```bash
docker compose up -d --build
```

### Using Docker directly

```bash
docker build -t bocchi .
docker run -d --name bocchi --env-file .env --restart unless-stopped bocchi
```

## Discord Bot Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application** and give it a name
3. Go to **Bot** → click **Reset Token** → copy the token
4. Enable **Message Content Intent** under **Privileged Gateway Intents**
5. Go to **OAuth2** → **URL Generator**:
   - Select scopes: `bot`, `applications.commands`
   - Select bot permissions: `Connect`, `Speak`, `Send Messages`, `Embed Links`
6. Copy the generated URL and open it to invite the bot to your server

## Spotify Setup (Optional)

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click **Create App**
3. Copy the **Client ID** and **Client Secret** to your `.env` file

## Project Structure

```
discord-music-bot/
├── bot/
│   ├── __init__.py
│   ├── config.py          # Configuration and environment variables
│   ├── embeds.py          # Discord embed builders
│   ├── main.py            # Bot entry point and setup
│   ├── music_player.py    # Music player and queue management
│   ├── spotify.py         # Spotify API integration
│   └── cogs/
│       ├── __init__.py
│       └── music.py       # Music slash commands
├── .dockerignore
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── run.py
└── README.md
```

## License

MIT
