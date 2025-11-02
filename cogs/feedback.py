import os

import httpx
import nextcord
from nextcord.ext import commands
from dotenv import load_dotenv

load_dotenv()


class Feedback(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.webhook_url = os.getenv("FEEDBACK_WEBHOOK_URL")

    @nextcord.slash_command(
        name="feedback",
        description="Submit feedback about the bot.",
    )
    async def feedback(
        self,
        interaction: nextcord.Interaction,
        name: str = nextcord.SlashOption(
            name="name",
            description="Your name",
            required=True,
        ),
        contact_method: str = nextcord.SlashOption(
            name="contact",
            description="Contact method (email, discord username, etc)",
            required=True,
        ),
        feedback_text: str = nextcord.SlashOption(
            name="feedback",
            description="Your feedback",
            required=True,
        ),
    ):
        """Submit feedback about the bot to the webhook."""
        if not self.webhook_url:
            await interaction.response.send_message(
                "❌ Feedback webhook is not configured. Please contact the bot administrator.",
                ephemeral=True,
            )
            return

        # Defer response since webhook call might take time
        await interaction.response.defer(ephemeral=True)

        # Prepare JSON payload
        payload = {
            "name": name,
            "contact_method": contact_method,
            "feedback": feedback_text,
            "discord_user": {
                "id": str(interaction.user.id),
                "username": interaction.user.name,
                "discriminator": getattr(interaction.user, "discriminator", None),
            },
            "guild_id": str(interaction.guild_id) if interaction.guild_id else None,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()

                await interaction.followup.send(
                    "✅ Feedback recorded successfully.", ephemeral=True
                )
        except httpx.HTTPStatusError as e:
            await interaction.followup.send(
                f"❌ Error submitting feedback: HTTP {e.response.status_code}",
                ephemeral=True,
            )
        except httpx.RequestError as e:
            await interaction.followup.send(
                f"❌ Error connecting to feedback service: {str(e)}",
                ephemeral=True,
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ Unexpected error: {str(e)}", ephemeral=True
            )
