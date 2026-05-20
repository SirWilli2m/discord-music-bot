from __future__ import annotations

import discord
from discord.ext import commands

from bot.config import DISCORD_TOKEN
from bot.logger import log


class Bocchi(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        await self.load_extension("bot.cogs.music")
        await self.tree.sync()
        log.info("Synced %d slash command(s)", len(self.tree.get_commands()))

    async def on_ready(self) -> None:
        log.info("Logged in as %s (ID: %s)", self.user, self.user.id)  # type: ignore[union-attr]
        log.info("Connected to %d guild(s)", len(self.guilds))
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="/play",
            )
        )


def main() -> None:
    if not DISCORD_TOKEN:
        log.error("DISCORD_TOKEN not set. Copy .env.example to .env and add your token.")
        return

    bot = Bocchi()
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
