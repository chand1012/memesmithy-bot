import io
import math
import os
from pathlib import Path

import nextcord
from nextcord.ext import commands

from lib.generate import generate_captions
from lib.img import generate_meme_image
from lib.templates import (
    get_all_templates,
    get_template_by_id,
    get_random_template,
    search_templates,
)


class Memes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(
        name="templates",
        description="View the templates available for generating memes. 10 per page.",
    )
    async def templates(
        self,
        interaction: nextcord.Interaction,
        page: int = nextcord.SlashOption(
            name="page",
            description="Page number to view (default: 1)",
            required=False,
            default=1,
        ),
    ):
        """View the templates available for generating memes. 10 per page, read from the templates.csv file."""
        templates = get_all_templates()

        if not templates:
            await interaction.response.send_message(
                "❌ No templates found in templates.csv!", ephemeral=True
            )
            return

        # Calculate pagination
        templates_per_page = 10
        total_pages = math.ceil(len(templates) / templates_per_page)

        # Validate page number
        if page < 1:
            page = 1
        elif page > total_pages:
            page = total_pages

        # Get templates for current page
        start_idx = (page - 1) * templates_per_page
        end_idx = start_idx + templates_per_page
        page_templates = templates[start_idx:end_idx]

        # Create embed
        embed = nextcord.Embed(
            title="📋 Meme Templates",
            description=f"Showing templates {start_idx + 1}-{min(end_idx, len(templates))} of {len(templates)}",
            color=nextcord.Color.blue(),
        )

        # Add each template to the embed
        for i, template in enumerate(page_templates, start=start_idx + 1):
            desc = (
                template.description[:100] if template.description else "No description"
            )
            # Truncate description if too long
            if len(desc) > 80:
                desc = desc[:77] + "..."

            value = f"**ID:** `{template.id}`\n{desc}"
            embed.add_field(name=f"{i}. {template.name}", value=value, inline=False)

        embed.set_footer(
            text=f"Page {page} of {total_pages} | Use /templates page:{page + 1} to navigate"
        )

        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(
        name="template",
        description="View a specific template image with its description.",
    )
    async def template(
        self,
        interaction: nextcord.Interaction,
        template_id: str = nextcord.SlashOption(
            name="template_id",
            description="The ID of the template to view",
            required=True,
        ),
    ):
        """View a specific template image with its description."""
        template_data = get_template_by_id(template_id)

        if not template_data:
            await interaction.response.send_message(
                f"❌ Template with ID `{template_id}` not found!", ephemeral=True
            )
            return

        images_dir = Path("images")
        if not images_dir.exists():
            await interaction.response.send_message(
                "❌ Images folder not found! Please run the download_images command first.",
                ephemeral=True,
            )
            return

        # Try to find the image file (could be .jpg, .png, etc.)
        image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
        image_path = None
        for ext in image_extensions:
            potential_path = images_dir / f"{template_id}{ext}"
            if potential_path.exists():
                image_path = potential_path
                break

        # If not found locally, try to get extension from URL
        if not image_path and template_data.image_url:
            url_ext = os.path.splitext(template_data.image_url)[1]
            potential_path = images_dir / f"{template_id}{url_ext}"
            if potential_path.exists():
                image_path = potential_path

        # Create embed with template information
        description = template_data.description or "No description available."

        # Truncate description if too long
        if len(description) > 2000:
            description = description[:1997] + "..."

        embed = nextcord.Embed(
            title=f"📋 {template_data.name}",
            description=description,
            color=nextcord.Color.blue(),
        )
        embed.add_field(name="Template ID", value=f"`{template_id}`", inline=True)

        # Add image if found
        if image_path and image_path.exists():
            file = nextcord.File(image_path, filename=image_path.name)
            embed.set_image(url=f"attachment://{image_path.name}")
            await interaction.response.send_message(embed=embed, file=file)
        else:
            # If image not found locally, use the URL from CSV if available
            if template_data.image_url:
                embed.set_image(url=template_data.image_url)
                embed.set_footer(text="⚠️ Image loaded from URL (not found locally)")
            else:
                embed.set_footer(text="⚠️ Image not found locally and no URL available")
            await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(
        name="search",
        description="Search for templates by keyword. Returns up to 10 matching templates.",
    )
    async def search(
        self,
        interaction: nextcord.Interaction,
        keyword: str = nextcord.SlashOption(
            name="keyword",
            description="Keyword to search for in template names and descriptions",
            required=True,
        ),
    ):
        """Search for templates by keyword in names and descriptions."""
        results = search_templates(keyword, max_results=10)

        if not results:
            await interaction.response.send_message(
                f"❌ No templates found matching '{keyword}'", ephemeral=True
            )
            return

        # Create embed
        embed = nextcord.Embed(
            title=f"🔍 Search Results for '{keyword}'",
            description=f"Found {len(results)} template(s)",
            color=nextcord.Color.blue(),
        )

        # Add each template to the embed
        for i, template in enumerate(results, start=1):
            desc = (
                template.description[:100] if template.description else "No description"
            )
            # Truncate description if too long
            if len(desc) > 80:
                desc = desc[:77] + "..."

            value = f"**ID:** `{template.id}`\n{desc}"
            embed.add_field(name=f"{i}. {template.name}", value=value, inline=False)

        if len(results) == 10:
            embed.set_footer(
                text="Showing top 10 results. Try a more specific search for better results."
            )

        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(
        name="generate",
        description="Generate a meme using a prompt and optional template ID.",
    )
    async def generate(
        self,
        interaction: nextcord.Interaction,
        prompt: str = nextcord.SlashOption(
            name="prompt",
            description="The prompt or text for the meme",
            required=True,
        ),
        template_id: str = nextcord.SlashOption(
            name="template_id",
            description="Template ID to use (leave empty for random)",
            required=False,
        ),
        watermark: bool = nextcord.SlashOption(
            name="watermark",
            description="Whether to add a watermark to the meme",
            required=False,
            default=True,
        ),
    ):
        """Generate a meme using the prompt and template_id. If no template_id is provided, use the random template."""
        template = (
            get_template_by_id(template_id) if template_id else get_random_template()
        )
        if not template:
            if template_id:
                await interaction.response.send_message(
                    f"❌ Template with ID `{template_id}` not found!", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ No templates available! Please ensure templates.csv has valid templates.",
                    ephemeral=True,
                )
            return

        try:
            # Generate captions using AI
            await interaction.response.defer()
            captions_dict = generate_captions(template.id, prompt)

            # Generate the meme image
            meme_image = generate_meme_image(
                template.id, captions_dict, "memesmithy.com" if watermark else None
            )

            # Convert PIL Image to bytes
            buffer = io.BytesIO()
            meme_image.save(buffer, format="PNG")
            buffer.seek(0)

            # Create Discord file and send
            file = nextcord.File(buffer, filename="meme.png")
            await interaction.followup.send(file=file)
        except ValueError as e:
            await interaction.followup.send(
                f"❌ Error generating meme: {str(e)}", ephemeral=True
            )
        except FileNotFoundError as e:
            await interaction.followup.send(
                f"❌ File not found: {str(e)}", ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ Unexpected error generating meme: {str(e)}", ephemeral=True
            )
