import os
import discord
from discord import app_commands
from discord.ext import commands
import google.generativeai as genai
import aiohttp

# === CONFIG ===
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN") or "YOUR_DISCORD_BOT_TOKEN"
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or "YOUR_GEMINI_API_KEY"

# Setup Discord
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Setup Gemini
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")  # fast + good for text

# --- Fetch character image (anime/manga via Jikan) ---
async def fetch_character_image(name: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.jikan.moe/v4/characters?q={name}&limit=1") as resp:
            if resp.status == 200:
                data = await resp.json()
                if data["data"]:
                    return data["data"][0]["images"]["jpg"]["image_url"]
    return None

# --- Character Description with Gemini ---
async def get_character_description(name: str):
    prompt = f"Give a short description of the character {name} from anime. Keep it under 80 words."
    response = model.generate_content(prompt)
    return response.text.strip()

# --- Autocomplete Suggestions from MAL ---
async def character_autocomplete(interaction: discord.Interaction, current: str):
    suggestions = []
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.jikan.moe/v4/characters?q={current}&limit=5") as resp:
            if resp.status == 200:
                data = await resp.json()
                for char in data["data"]:
                    suggestions.append(app_commands.Choice(name=char["name"], value=char["name"]))
    return suggestions

# === Slash Command ===
@bot.tree.command(name="describe", description="Get a short description of an anime character")
@app_commands.autocomplete(name=character_autocomplete)
async def describe(interaction: discord.Interaction, name: str):
    await interaction.response.defer()

    desc = await get_character_description(name)
    image_url = await fetch_character_image(name)

    embed = discord.Embed(title=f"{name}", description=desc, color=0x00ffcc)
    if image_url:
        embed.set_thumbnail(url=image_url)

    await interaction.followup.send(embed=embed)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

bot.run(DISCORD_TOKEN)
