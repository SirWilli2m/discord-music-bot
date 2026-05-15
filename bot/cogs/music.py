from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from bot.embeds import (
    added_to_queue_embed,
    error_embed,
    now_playing_embed,
    queue_embed,
)
from bot.music_player import MusicPlayer
from bot.spotify import SpotifyClient


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.player = MusicPlayer()
        self.spotify = SpotifyClient()

    async def _ensure_voice(self, interaction: discord.Interaction) -> discord.VoiceClient | None:
        if not interaction.guild:
            await interaction.followup.send(
                embed=error_embed("This command can only be used in a server.")
            )
            return None

        member = interaction.guild.get_member(interaction.user.id)
        if not member or not member.voice or not member.voice.channel:
            await interaction.followup.send(embed=error_embed("You need to be in a voice channel."))
            return None

        voice_client = interaction.guild.voice_client

        if voice_client and isinstance(voice_client, discord.VoiceClient):
            if voice_client.channel != member.voice.channel:
                await voice_client.move_to(member.voice.channel)
            return voice_client

        channel = member.voice.channel
        try:
            voice_client = await channel.connect(self_deaf=True)
        except Exception:
            await interaction.followup.send(
                embed=error_embed("Failed to connect to your voice channel.")
            )
            return None

        return voice_client  # type: ignore[return-value]

    @app_commands.command(name="play", description="Play a song from YouTube or Spotify")
    @app_commands.describe(query="YouTube/Spotify URL or search query")
    async def play(self, interaction: discord.Interaction, query: str) -> None:
        await interaction.response.defer()

        voice_client = await self._ensure_voice(interaction)
        if not voice_client or not interaction.guild:
            return

        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            return

        guild_player = self.player.get_player(interaction.guild.id)

        # Handle Spotify URLs
        if self.spotify.is_spotify_url(query):
            if not self.spotify.enabled:
                await interaction.followup.send(
                    embed=error_embed(
                        "Spotify support is not configured. "
                        "Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in your .env file."
                    )
                )
                return

            search_queries = self.spotify.get_tracks_from_url(query)
            if not search_queries:
                await interaction.followup.send(
                    embed=error_embed("Could not find any tracks from that Spotify link.")
                )
                return

            await interaction.followup.send(
                f"Processing **{len(search_queries)}** track(s) from Spotify..."
            )

            added = 0
            for sq in search_queries:
                entries = await self.player.extract_info(f"ytsearch:{sq}")
                if entries:
                    track = await self.player.create_track(entries[0], member)
                    if track:
                        guild_player.queue.append(track)
                        added += 1

            if added == 0:
                await interaction.channel.send(  # type: ignore[union-attr]
                    embed=error_embed("Could not resolve any Spotify tracks.")
                )
                return

            await interaction.channel.send(  # type: ignore[union-attr]
                f"Added **{added}** track(s) to the queue from Spotify."
            )

            if not voice_client.is_playing() and not voice_client.is_paused():
                guild_player.current = guild_player.queue.pop(0)
                source = self.player.create_source(guild_player.current)

                def after(error: Exception | None) -> None:
                    if error:
                        print(f"Player error: {error}")
                    import asyncio

                    asyncio.run_coroutine_threadsafe(
                        self.player.play_next(interaction.guild),  # type: ignore[arg-type]
                        self.bot.loop,
                    )

                voice_client.play(source, after=after)
                await interaction.channel.send(  # type: ignore[union-attr]
                    embed=now_playing_embed(guild_player.current)
                )
            return

        # Handle YouTube URLs and search queries
        entries = await self.player.extract_info(query)
        if not entries:
            await interaction.followup.send(embed=error_embed("No results found for your query."))
            return

        if len(entries) > 1:
            await interaction.followup.send(
                f"Processing **{len(entries)}** track(s) from playlist..."
            )
            added = 0
            for entry in entries:
                track = await self.player.create_track(entry, member)
                if track:
                    guild_player.queue.append(track)
                    added += 1

            if added == 0:
                await interaction.channel.send(  # type: ignore[union-attr]
                    embed=error_embed("Could not load any tracks from the playlist.")
                )
                return

            await interaction.channel.send(  # type: ignore[union-attr]
                f"Added **{added}** track(s) to the queue."
            )

            if not voice_client.is_playing() and not voice_client.is_paused():
                guild_player.current = guild_player.queue.pop(0)
                source = self.player.create_source(guild_player.current)

                def after(error: Exception | None) -> None:
                    if error:
                        print(f"Player error: {error}")
                    import asyncio

                    asyncio.run_coroutine_threadsafe(
                        self.player.play_next(interaction.guild),  # type: ignore[arg-type]
                        self.bot.loop,
                    )

                voice_client.play(source, after=after)
                await interaction.channel.send(  # type: ignore[union-attr]
                    embed=now_playing_embed(guild_player.current)
                )
            return

        track = await self.player.create_track(entries[0], member)
        if not track:
            await interaction.followup.send(embed=error_embed("Failed to load that track."))
            return

        if voice_client.is_playing() or voice_client.is_paused():
            guild_player.queue.append(track)
            position = len(guild_player.queue)
            await interaction.followup.send(embed=added_to_queue_embed(track, position))
        else:
            guild_player.current = track
            source = self.player.create_source(track)

            def after(error: Exception | None) -> None:
                if error:
                    print(f"Player error: {error}")
                import asyncio

                asyncio.run_coroutine_threadsafe(
                    self.player.play_next(interaction.guild),  # type: ignore[arg-type]
                    self.bot.loop,
                )

            voice_client.play(source, after=after)
            await interaction.followup.send(embed=now_playing_embed(track))

    @app_commands.command(name="skip", description="Skip the current song")
    async def skip(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        if not interaction.guild or not interaction.guild.voice_client:
            await interaction.followup.send(embed=error_embed("Not currently playing anything."))
            return

        voice_client = interaction.guild.voice_client
        if isinstance(voice_client, discord.VoiceClient) and voice_client.is_playing():
            guild_player = self.player.get_player(interaction.guild.id)
            guild_player.loop = False
            voice_client.stop()
            await interaction.followup.send("⏭️ Skipped!")
        else:
            await interaction.followup.send(embed=error_embed("Nothing is playing right now."))

    @app_commands.command(name="pause", description="Pause the current song")
    async def pause(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        if not interaction.guild or not interaction.guild.voice_client:
            await interaction.followup.send(embed=error_embed("Not currently playing anything."))
            return

        voice_client = interaction.guild.voice_client
        if isinstance(voice_client, discord.VoiceClient) and voice_client.is_playing():
            voice_client.pause()
            await interaction.followup.send("⏸️ Paused!")
        else:
            await interaction.followup.send(embed=error_embed("Nothing is playing right now."))

    @app_commands.command(name="resume", description="Resume the paused song")
    async def resume(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        if not interaction.guild or not interaction.guild.voice_client:
            await interaction.followup.send(embed=error_embed("Not currently playing anything."))
            return

        voice_client = interaction.guild.voice_client
        if isinstance(voice_client, discord.VoiceClient) and voice_client.is_paused():
            voice_client.resume()
            await interaction.followup.send("▶️ Resumed!")
        else:
            await interaction.followup.send(embed=error_embed("Nothing is paused right now."))

    @app_commands.command(name="stop", description="Stop playing and clear the queue")
    async def stop(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        if not interaction.guild or not interaction.guild.voice_client:
            await interaction.followup.send(embed=error_embed("Not currently playing anything."))
            return

        voice_client = interaction.guild.voice_client
        guild_player = self.player.get_player(interaction.guild.id)
        guild_player.clear()

        if isinstance(voice_client, discord.VoiceClient):
            voice_client.stop()
            await voice_client.disconnect()

        await interaction.followup.send("⏹️ Stopped and cleared the queue!")

    @app_commands.command(name="queue", description="Show the current music queue")
    async def queue(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        if not interaction.guild:
            await interaction.followup.send(
                embed=error_embed("This command can only be used in a server.")
            )
            return

        guild_player = self.player.get_player(interaction.guild.id)
        embed = queue_embed(guild_player.current, guild_player.queue, guild_player.loop)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="nowplaying", description="Show the currently playing song")
    async def nowplaying(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        if not interaction.guild:
            await interaction.followup.send(
                embed=error_embed("This command can only be used in a server.")
            )
            return

        guild_player = self.player.get_player(interaction.guild.id)
        if guild_player.current:
            await interaction.followup.send(embed=now_playing_embed(guild_player.current))
        else:
            await interaction.followup.send(embed=error_embed("Nothing is playing right now."))

    @app_commands.command(name="loop", description="Toggle loop for the current song")
    async def loop(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        if not interaction.guild:
            await interaction.followup.send(
                embed=error_embed("This command can only be used in a server.")
            )
            return

        guild_player = self.player.get_player(interaction.guild.id)
        guild_player.loop = not guild_player.loop
        status = "enabled" if guild_player.loop else "disabled"
        await interaction.followup.send(f"🔁 Loop **{status}**!")

    @app_commands.command(name="shuffle", description="Shuffle the queue")
    async def shuffle(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        if not interaction.guild:
            await interaction.followup.send(
                embed=error_embed("This command can only be used in a server.")
            )
            return

        guild_player = self.player.get_player(interaction.guild.id)
        if len(guild_player.queue) < 2:
            await interaction.followup.send(
                embed=error_embed("Not enough songs in the queue to shuffle.")
            )
            return

        import random

        random.shuffle(guild_player.queue)
        await interaction.followup.send("🔀 Queue shuffled!")

    @app_commands.command(name="remove", description="Remove a song from the queue by position")
    @app_commands.describe(position="Position of the song in the queue (starting from 1)")
    async def remove(self, interaction: discord.Interaction, position: int) -> None:
        await interaction.response.defer()

        if not interaction.guild:
            await interaction.followup.send(
                embed=error_embed("This command can only be used in a server.")
            )
            return

        guild_player = self.player.get_player(interaction.guild.id)
        if position < 1 or position > len(guild_player.queue):
            await interaction.followup.send(
                embed=error_embed(f"Invalid position. Queue has {len(guild_player.queue)} song(s).")
            )
            return

        removed = guild_player.queue.pop(position - 1)
        await interaction.followup.send(f"Removed **{removed.title}** from the queue.")

    @app_commands.command(name="disconnect", description="Disconnect the bot from voice channel")
    async def disconnect(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        if not interaction.guild or not interaction.guild.voice_client:
            await interaction.followup.send(embed=error_embed("I'm not in a voice channel."))
            return

        voice_client = interaction.guild.voice_client
        guild_player = self.player.get_player(interaction.guild.id)
        guild_player.clear()

        if isinstance(voice_client, discord.VoiceClient):
            voice_client.stop()
            await voice_client.disconnect()

        await interaction.followup.send("👋 Disconnected!")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Music(bot))
