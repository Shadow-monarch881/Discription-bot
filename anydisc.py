import os
import discord
from discord import app_commands
from discord.ext import commands
import google.generativeai as genai
import aiohttp
from flask import Flask
from threading import Thread

# === CONFIG ===
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN") or "YOUR_DISCORD_BOT_TOKEN"
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or "YOUR_GEMINI_API_KEY"

# Setup Discord
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Setup Gemini
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")  # fast + good for text

# --- Flask Keep Alive Webserver ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

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
async def fetch_anime_data(name: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.jikan.moe/v4/anime?q={name}&limit=1") as resp:
            if resp.status == 200:
                data = await resp.json()
                if data["data"]:
                    return data["data"][0]
    return None

@bot.tree.command(name="anime", description="Get anime details")
async def anime(interaction: discord.Interaction, name: str):
    await interaction.response.defer()

    anime = await fetch_anime_data(name)
    if not anime:
        await interaction.followup.send("❌ Anime not found.")
        return

    # Description with cutoff
    synopsis = anime["synopsis"][:300] + "..." if len(anime["synopsis"]) > 300 else anime["synopsis"]

    embed = discord.Embed(
        title=f"{anime['title']} ({anime['type']})",
        description=synopsis,
        url=anime["url"],
        color=0x00ffcc
    )

    # Big image
    if anime["images"]["jpg"]["large_image_url"]:
        embed.set_image(url=anime["images"]["jpg"]["large_image_url"])

    # Add info fields
    embed.add_field(name="Episodes", value=anime.get("episodes", "N/A"))
    embed.add_field(name="Status", value=anime.get("status", "N/A"))
    embed.add_field(name="Aired", value=f"{anime['aired']['string']}", inline=False)
    embed.add_field(name="Score", value=anime.get("score", "N/A"))
    embed.add_field(name="Genres", value=", ".join([g["name"] for g in anime["genres"]]), inline=False)

    # More info links
    embed.add_field(
        name="Find Out More",
        value=f"[MyAnimeList]({anime['url']})",
        inline=False
    )

    await interaction.followup.send(embed=embed)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

# === START BOT + KEEP ALIVE ===
keep_alive()
bot.run(DISCORD_TOKEN)

