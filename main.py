import fire
import nextcord
from nextcord.ext import commands

from src.agents.tools import get_image_text, get_str_bounding_box
from src.cogs.generator import Generator
from src.lib.env import DISCORD_TOKEN


def init_bot():
    intents = nextcord.Intents.default()
    bot = commands.Bot(command_prefix="!", intents=intents)
    bot.add_cog(Generator(bot))
    bot.run(DISCORD_TOKEN)


def describe_img(image_url: str):
    texts = get_image_text(image_url)
    for text in texts:
        print(text)
        print(get_str_bounding_box(image_url, text))


if __name__ == "__main__":
    fire.Fire({
        "bot": init_bot,
        "get_image_text": describe_img,
    })
