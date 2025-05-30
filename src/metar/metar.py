import os
import re
import xml.etree.ElementTree as ET

import discord
from discord.ext import commands, tasks
import requests

# --- Configuration ---
ICAO_REGEX = r"^[A-Z]{4}$"
BOT_TOKEN = os.getenv('DISCORD_TOKEN')
if not BOT_TOKEN:
    raise ValueError("DISCORD_TOKEN not found in environment variables.  Please set it.")

# --- Bot Setup ---
intents = discord.Intents.default()  # Or Intents.all() if you need all.  Use default for basic functionality.
intents.message_content = True  #  Required for reading message content
bot = commands.Bot(command_prefix="/", intents=intents)  # Use command_prefix as a string


# --- Events ---
@bot.event
async def on_ready():
    """Prints a message when the bot connects to Discord."""
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")


# --- Commands ---
@bot.command(name="weather", description="Get METAR and TAF data for an ICAO airport from metartaf.ru")
async def weather_command(ctx: commands.Context, icao: str):
    """
    Gets METAR and TAF data for a given ICAO airport from metartaf.ru.

    Args:
        ctx: The command context.
        icao: The ICAO airport code (e.g., UUDD).
    """
    icao = icao.upper()  # Consistent capitalization for comparison.

    if not re.match(ICAO_REGEX, icao):
        await ctx.send("Invalid ICAO code format. Please use a 4-letter code (e.g., UUDD).")
        return  # Exit if ICAO is invalid.

    try:
        url = f"http://metartaf.ru/{icao}.xml"  # API URL
        response = requests.get(url, timeout=10)  # Add timeout to prevent hangs
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)

        xml_content = response.text  # XML DATA

        # Parse the XML
        try:  # Handle potential XML parsing errors.
            root = ET.fromstring(xml_content)
        except ET.ParseError:
            await ctx.send(f"Error parsing XML data for {icao}.  The server might be down or the data is malformed.")
            return

        # Extract data (use .text for consistent handling)
        metar_element = root.find('metar')
        taf_element = root.find('taf')
        metar = metar_element.text if metar_element is not None else None
        taf = taf_element.text if taf_element is not None else None


        # Format the output (only include fields if they exist) using an Embed.
        embed = discord.Embed(title=f"Weather Data for {icao}", color=discord.Color.blue())  # Use an Embed
        if metar:
            embed.add_field(name="METAR", value=metar, inline=False)
        if taf:
            embed.add_field(name="TAF", value=taf, inline=False)

        if not embed.fields: # if no fields were added (no data).
            await ctx.send(f"No METAR or TAF data found for {icao}.")  # If it's all null
        else:
            await ctx.send(embed=embed)


    except requests.exceptions.RequestException as e:
        await ctx.send(f"Error fetching data for {icao}.  Check the ICAO code, or the metartaf.ru service may be unavailable.  Error: {e}")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred for {icao}: {e}")


# --- Run the bot ---
bot.run(BOT_TOKEN)