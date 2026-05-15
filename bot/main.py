from __future__ import annotations

import discord
from discord.ext import commands

from bot.config import DISCORD_TOKEN


class Bocchi(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        await self.load_extension("bot.cogs.music")
        await self.tree.sync()
        print(f"Synced {len(self.tree.get_commands())} slash command(s)")

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user} (ID: {self.user.id})")  # type: ignore[union-attr]
        print(f"Connected to {len(self.guilds)} guild(s)")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="/play",
            )
        )


def main() -> None:
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN not set. Copy .env.example to .env and add your token.")
        return

    bot = Bocchi()
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
