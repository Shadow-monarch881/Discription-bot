import discord
from discord.ext import commands
import aiohttp

# --- CONFIG ---
TOKEN = "YOUR_DISCORD_BOT_TOKEN"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- FETCH CHARACTER INFO ---
async def fetch_character(name: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.jikan.moe/v4/characters?q={name}&limit=1") as resp:
            if resp.status == 200:
                data = await resp.json()
                if data["data"]:
                    char = data["data"][0]
                    return {
                        "name": char["name"],
                        "image": char["images"]["jpg"]["image_url"],
                        "description": char["about"][:400] + "..." if char["about"] else "No description available",
                        "url": char["url"]
                    }
    return None

# --- FETCH ANIME INFO ---
async def fetch_anime(name: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.jikan.moe/v4/anime?q={name}&limit=1") as resp:
            if resp.status == 200:
                data = await resp.json()
                if data["data"]:
                    anime = data["data"][0]
                    return {
                        "title": anime["title"],
                        "type": anime.get("type", "N/A"),
                        "episodes": anime.get("episodes", "N/A"),
                        "status": anime.get("status", "N/A"),
                        "score": anime.get("score", "N/A"),
                        "aired": anime["aired"]["string"] if anime.get("aired") else "N/A",
                        "genres": ", ".join([g["name"] for g in anime.get("genres", [])]),
                        "synopsis": anime.get("synopsis", "No synopsis available")[:400] + "...",
                        "image": anime["images"]["jpg"]["large_image_url"] if anime["images"]["jpg"].get("large_image_url") else None,
                        "url": anime.get("url", "")
                    }
    return None

# --- COMMANDS ---

@bot.command(name="character")
async def character(ctx, *, name: str):
    char = await fetch_character(name)
    if not char:
        return await ctx.send("❌ Character not found.")
    
    embed = discord.Embed(title=char["name"], description=char["description"], url=char["url"], color=0x00ffcc)
    embed.set_image(url=char["image"])
    await ctx.send(embed=embed)

@bot.command(name="anime")
async def anime(ctx, *, name: str):
    ani = await fetch_anime(name)
    if not ani:
        return await ctx.send("❌ Anime not found.")
    
    embed = discord.Embed(title=f"{ani['title']} ({ani['type']})", description=ani["synopsis"], url=ani["url"], color=0x00ffcc)
    if ani["image"]:
        embed.set_image(url=ani["image"])
    
    embed.add_field(name="Episodes", value=ani["episodes"])
    embed.add_field(name="Status", value=ani["status"])
    embed.add_field(name="Aired", value=ani["aired"], inline=False)
    embed.add_field(name="Score", value=ani["score"])
    embed.add_field(name="Genres", value=ani["genres"], inline=False)
    
    await ctx.send(embed=embed)

# --- READY ---
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

bot.run(TOKEN)
