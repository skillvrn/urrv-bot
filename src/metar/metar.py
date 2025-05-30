import os
import re
import xml.etree.ElementTree as ET

import discord
from discord.ext import commands

# --- Configuration ---
ICAO_REGEX = r"^[A-Z]{4}$"
BOT_TOKEN = os.getenv('DISCORD_TOKEN')
if not BOT_TOKEN:
    raise ValueError(
        "DISCORD_TOKEN not found in environment variables. Please set it.")

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)


# --- Events ---
@bot.event
async def on_ready():
    """Prints a message when the bot connects to Discord."""
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")


# --- Commands ---
@bot.command(name="weather",
             description="Get METAR and TAF data for an ICAO airport from "
                         "metartaf.ru")
async def weather_command(ctx: commands.Context, icao: str):
    """Gets METAR and TAF data for a given ICAO airport from metartaf.ru.

    Args:
        ctx: The command context.
        icao: The ICAO airport code (e.g., UUDD).
    """
    icao = icao.upper()

    if not re.match(ICAO_REGEX, icao):
        await ctx.send("Invalid ICAO code format. Please use a 4-letter code "
                       "(e.g., UUDD).")
        return

    try:
        url = f"http://metartaf.ru/{icao}.xml"
        import requests  # Move import inside the try block
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        xml_content = response.text

        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError:
            await ctx.send(f"Error parsing XML data for {icao}. The server "
                           "might be down or the data is malformed.")
            return

        metar_element = root.find('metar')
        taf_element = root.find('taf')
        metar = metar_element.text if metar_element is not None else None
        taf = taf_element.text if taf_element is not None else None

        embed = discord.Embed(title=f"Weather Data for {icao}",
                              color=discord.Color.blue())
        if metar:
            embed.add_field(name="METAR", value=metar, inline=False)
        if taf:
            embed.add_field(name="TAF", value=taf, inline=False)

        if not embed.fields:
            await ctx.send(f"No METAR or TAF data found for {icao}.")
        else:
            await ctx.send(embed=embed)

    except requests.exceptions.RequestException as e:
        await ctx.send(
            f"Error fetching data for {icao}. Check the ICAO code, or the "
            "metartaf.ru service may be unavailable. Error: {e}")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred for {icao}: {e}")


# --- Run the bot ---
bot.run(BOT_TOKEN)