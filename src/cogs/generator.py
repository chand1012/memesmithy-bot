import random
import json

from nextcord.ext import commands
import nextcord
import supabase

from src.lib.env import SUPABASE_URL, SUPABASE_KEY, SUPABASE_PASSWORD, SUPABASE_USERNAME


class Generator(commands.Cog):
    def __init__(self, bot: nextcord.Client):
        self.bot = bot
        self.supabase = supabase.create_client(
            SUPABASE_URL, SUPABASE_KEY, supabase.ClientOptions(function_client_timeout=180))
        self.auth_response = self.supabase.auth.sign_in_with_password({
            "email": SUPABASE_USERNAME,
            "password": SUPABASE_PASSWORD
        })

    @nextcord.slash_command(name="meme", description="Generate a meme")
    async def meme(self, interaction: nextcord.Interaction, prompt: str = nextcord.SlashOption(description="The prompt for the meme", required=True), template_id: str | None = nextcord.SlashOption(description="The meme id to use", required=False, default=None)):
        await interaction.response.defer()

        if not template_id:
            # get all the templates from the database
            templates = self.supabase.table("templates").select("id").execute()
            template_ids = [template["id"] for template in templates.data]

            # get a random template
            template_id = random.choice(template_ids)
        else:
            template_id = template_id.strip()
            # verify that the template id is valid
            templates = self.supabase.table("templates").select("id").eq(
                'id', template_id).execute()
            if len(templates.data) == 0:
                await interaction.followup.send(embed=nextcord.Embed(
                    title="Invalid template id", description="The template id you provided is invalid. Please try again."))
                return

        response = self.supabase.functions.invoke("generate_meme", {
            "body": {
                "meme_id": template_id,
                "prompt": prompt
            }
        })

        response = json.loads(response)
        # {"0":{"id":"d9b0a5ca-bb31-41ab-b6ef-74e923f8786d","template_id":"f1a96777-3e6c-427f-ba9d-eaaa80857d03","user_id":"3bf70b57-a422-44fe-87bf-ae42c9b4cf2f","image_url":"https://i.memesmithy.com/memes/d9b0a5ca-bb31-41ab-b6ef-74e923f8786d.jpg","prompt":"Chandler is making more AI tools","boxes":[{"h":84,"w":594,"x":17,"y":13,"font":"impact","text":"Chandler making more AI tools be like","color":"white","border":"black"},{"h":107,"w":589,"x":21,"y":346,"font":"impact","text":"You get a model! And you get a model! Everybody gets a neural network!","color":"white","border":"black"}],"public":true,"caption":null,"created_at":"2025-03-31T03:19:31.100269+00:00","updated_at":"2025-03-31T03:19:31.100269+00:00","deleted_at":null},"width":620,"height":464}

        # construct an embed with the image and the prompt
        # link to the meme on memesmithy via https://app.memesmithy.com/memes/{id}
        embed = nextcord.Embed(
            title=response["0"]["prompt"], url=f"https://app.memesmithy.com/memes/{response['0']['id']}")
        embed.set_image(url=response["0"]["image_url"])

        # send the embed to the user
        await interaction.followup.send(embed=embed)

    @nextcord.slash_command(name="templates", description="Get a list of templates")
    async def templates(self, interaction: nextcord.Interaction, page: int = nextcord.SlashOption(description="The page number to get", required=False, default=1)):
        await interaction.response.defer()

        # we'll always show 10 templates per page
        start = (page - 1) * 10
        end = start + 10

        # get the templates from the database
        templates = self.supabase.table("templates").select(
            "*").range(start, end).order("created_at", desc=False).execute()

        # send as well formatted markdown with a link to create via web app
        # as well as the ID to use for the /meme command.
        # include the name (which should be a link to the template), the ID

        body = ""
        for template in templates.data:
            body += f"**[{template['name']}](https://app.memesmithy.com/create/generate/{template['id']})**\n"
            body += f"ID: `{template['id']}`\n"

        # add a footer with the page number and the total number of pages

        await interaction.followup.send(body)
