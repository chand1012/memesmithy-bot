import fire
import nextcord
from nextcord.ext import commands

from src.cogs.generator import Generator
from src.lib.env import DISCORD_TOKEN


def init_bot():
    intents = nextcord.Intents.default()
    bot = commands.Bot(command_prefix="!", intents=intents)
    bot.add_cog(Generator(bot))
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    fire.Fire({
        "bot": init_bot
    })
