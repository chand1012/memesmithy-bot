import asyncio
import os
import sys

import nextcord
from dotenv import load_dotenv
from nextcord.ext import commands


"""Start the Discord bot and load all cogs."""
# Load environment variables from .env file
load_dotenv()

# Get bot token from environment variable
token = os.getenv("DISCORD_TOKEN") or os.getenv("BOT_TOKEN")
if not token:
    print("❌ Error: DISCORD_TOKEN or BOT_TOKEN environment variable not set!")
    print("Please set your Discord bot token in a .env file or environment variable.")
    sys.exit(1)

# Create bot instance
intents = nextcord.Intents.default()

bot_instance = commands.Bot(
    intents=intents,
)


async def load_cogs():
    """Load all cogs."""
    # Load the memes cog
    try:
        from cogs.memes import Memes

        bot_instance.add_cog(Memes(bot_instance))
        print("✅ Loaded cogs.memes")
    except Exception as e:
        print(f"❌ Failed to load cogs.memes: {e}")

    # Load the send cog
    try:
        from cogs.send import Send

        bot_instance.add_cog(Send(bot_instance))
        print("✅ Loaded cogs.send")
    except Exception as e:
        print(f"❌ Failed to load cogs.send: {e}")


@bot_instance.event
async def on_ready():
    """Called when the bot is ready."""
    print(f"✅ Bot is ready! Logged in as {bot_instance.user}")
    print(f"   Bot ID: {bot_instance.user.id}")
    print(f"   Guilds: {len(bot_instance.guilds)}")


@bot_instance.event
async def on_application_command_error(
    interaction: nextcord.Interaction, error: nextcord.ApplicationError
):
    """Handle slash command errors."""
    print(
        f"❌ Error in slash command {interaction.data.get('name', 'unknown')}: {error}"
    )
    if interaction.response.is_done():
        await interaction.followup.send(
            f"❌ An error occurred: {error}", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"❌ An error occurred: {error}", ephemeral=True
        )


# Load cogs and run bot
async def main():
    await load_cogs()
    await bot_instance.start(token)


# Run the bot
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\n🛑 Bot stopped by user")
except Exception as e:
    print(f"❌ Fatal error: {e}")
