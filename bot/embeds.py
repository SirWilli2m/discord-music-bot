from __future__ import annotations

import discord

from bot.music_player import Track


def now_playing_embed(track: Track) -> discord.Embed:
    embed = discord.Embed(
        title="Now Playing 🎵",
        description=f"[{track.title}]({track.url})",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Duration", value=track.duration_str, inline=True)
    embed.add_field(name="Requested by", value=track.requester.display_name, inline=True)
    if track.thumbnail:
        embed.set_thumbnail(url=track.thumbnail)
    return embed


def added_to_queue_embed(track: Track, position: int) -> discord.Embed:
    embed = discord.Embed(
        title="Added to Queue",
        description=f"[{track.title}]({track.url})",
        color=discord.Color.green(),
    )
    embed.add_field(name="Duration", value=track.duration_str, inline=True)
    embed.add_field(name="Position", value=str(position), inline=True)
    embed.add_field(name="Requested by", value=track.requester.display_name, inline=True)
    if track.thumbnail:
        embed.set_thumbnail(url=track.thumbnail)
    return embed


def queue_embed(current: Track | None, queue: list[Track], loop: bool) -> discord.Embed:
    embed = discord.Embed(
        title="Music Queue",
        color=discord.Color.blurple(),
    )

    if current:
        embed.add_field(
            name="Now Playing",
            value=f"[{current.title}]({current.url}) [{current.duration_str}]",
            inline=False,
        )

    if queue:
        lines: list[str] = []
        for i, track in enumerate(queue[:10], start=1):
            lines.append(f"`{i}.` [{track.title}]({track.url}) [{track.duration_str}]")
        if len(queue) > 10:
            lines.append(f"\n... and {len(queue) - 10} more")
        embed.add_field(name="Up Next", value="\n".join(lines), inline=False)
    else:
        embed.add_field(name="Up Next", value="Queue is empty", inline=False)

    if loop:
        embed.set_footer(text="🔁 Loop is enabled")

    return embed


def error_embed(message: str) -> discord.Embed:
    return discord.Embed(
        title="Error",
        description=message,
        color=discord.Color.red(),
    )
