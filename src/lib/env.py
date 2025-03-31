import os

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_USERNAME = os.getenv("SUPABASE_USERNAME")
SUPABASE_PASSWORD = os.getenv("SUPABASE_PASSWORD")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
