from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

import discord
import yt_dlp

from bot.config import FFMPEG_OPTIONS, YDL_OPTIONS


@dataclass
class Track:
    title: str
    url: str
    stream_url: str
    duration: int
    thumbnail: str
    requester: discord.Member

    @property
    def duration_str(self) -> str:
        minutes, seconds = divmod(self.duration, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"


@dataclass
class GuildPlayer:
    guild_id: int
    queue: list[Track] = field(default_factory=list)
    current: Track | None = None
    loop: bool = False
    volume: float = 0.5
    _play_next_event: asyncio.Event = field(default_factory=asyncio.Event)

    def clear(self) -> None:
        self.queue.clear()
        self.current = None
        self.loop = False


class MusicPlayer:
    def __init__(self) -> None:
        self.players: dict[int, GuildPlayer] = {}

    def get_player(self, guild_id: int) -> GuildPlayer:
        if guild_id not in self.players:
            self.players[guild_id] = GuildPlayer(guild_id=guild_id)
        return self.players[guild_id]

    async def extract_info(self, query: str) -> list[dict]:
        loop = asyncio.get_event_loop()
        ydl_opts = {**YDL_OPTIONS, "extract_flat": "in_playlist"}

        def _extract() -> dict | None:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(query, download=False)

        data = await loop.run_in_executor(None, _extract)
        if data is None:
            return []

        entries: list[dict] = []
        if "entries" in data:
            for entry in data["entries"]:
                if entry:
                    entries.append(entry)
        else:
            entries.append(data)

        return entries

    async def resolve_stream_url(self, url: str) -> dict | None:
        loop = asyncio.get_event_loop()
        ydl_opts = {**YDL_OPTIONS, "extract_flat": False}

        def _extract() -> dict | None:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        return await loop.run_in_executor(None, _extract)

    async def create_track(self, entry: dict, requester: discord.Member) -> Track | None:
        url = entry.get("webpage_url") or entry.get("url", "")
        if entry.get("_type") == "url" or not entry.get("url", "").startswith("http"):
            info = await self.resolve_stream_url(url)
            if info is None:
                return None
            entry = info

        stream_url = entry.get("url", "")
        if not stream_url:
            return None

        return Track(
            title=entry.get("title", "Unknown"),
            url=entry.get("webpage_url", url),
            stream_url=stream_url,
            duration=entry.get("duration", 0) or 0,
            thumbnail=entry.get("thumbnail", ""),
            requester=requester,
        )

    def create_source(self, track: Track) -> discord.FFmpegOpusAudio:
        return discord.FFmpegOpusAudio(track.stream_url, **FFMPEG_OPTIONS)

    async def play_next(self, guild: discord.Guild) -> None:
        player = self.get_player(guild.id)
        voice_client = guild.voice_client

        if not isinstance(voice_client, discord.VoiceClient) or not voice_client.is_connected():
            player.clear()
            return

        if player.loop and player.current:
            info = await self.resolve_stream_url(player.current.url)
            if info:
                player.current.stream_url = info.get("url", player.current.stream_url)
        elif player.queue:
            player.current = player.queue.pop(0)
        else:
            player.current = None
            return

        if player.current is None:
            return

        source = self.create_source(player.current)

        def after_playing(error: Exception | None) -> None:
            if error:
                print(f"Player error: {error}")
            asyncio.run_coroutine_threadsafe(self.play_next(guild), asyncio.get_event_loop())

        voice_client.play(source, after=after_playing)
