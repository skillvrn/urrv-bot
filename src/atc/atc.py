import os
import datetime
import discord
from discord.ext import commands, tasks
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re  # Импортируем модуль re

# --- Configuration ---
BOT_PREFIX = "!"
POSITION_ANNOUNCEMENT_CHANNEL_ID: Optional[int] = int(
    os.getenv('DISCORD_POSITION_ANNOUNCEMENT_CHANNEL_ID') or 0)
XR_SITE_URL = "https://xr.ivao.aero/"
CHECK_INTERVAL_SECONDS = 60
BOT_COLOR = discord.Color.green()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN not found in environment variables.")

# --- Bot Initialization ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# --- Global Variables ---
monitored_positions: Dict[str, datetime.datetime] = {}
announcement_message: Optional[discord.Message] = None

# --- Helper Functions ---


async def get_positions_from_site(
        session: aiohttp.ClientSession) -> List[Dict[str, str]]:
    """Retrieves positions and their data."""
    try:
        async with session.get(XR_SITE_URL, timeout=10) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                table = soup.find("table")
                if not table:
                    print("Table not found!")
                    return []

                positions_data: List[Dict[str, str]] = []
                for row in table.find_all("tr")[1:]:
                    cells = row.find_all("td")
                    if cells and len(cells) >= 2:
                        position = cells[0].text.strip()
                        if position.startswith("UR"):
                            data = cells[1].text.strip()
                            positions_data.append(
                                {"position": position, "data": data})
                return positions_data
            else:
                print(f"HTTP Error: {response.status}")
                return []
    except aiohttp.ClientError as e:
        print(f"Connection Error: {e}")
        return []
    except Exception as e:
        print(f"Scraping Error: {e}")
        return []


async def build_position_list_embed(
        positions_data: List[Dict[str, str]]) -> discord.Embed:
    """Builds the embed with formatted position data."""
    embed = discord.Embed(
        title="✈ **Active URRV FIR Positions** ✈",
        color=BOT_COLOR,
        timestamp=datetime.datetime.now()
    )
    if positions_data:
        for item in positions_data:
            position = item['position']
            data = item['data']

            # Extract the VID and Frequency
            # Find 6 digits, then frequency before "Mhz"
            match = re.search(r"(\d{6}).*?(\d+\.\d+)Mhz", data)

            if match:
                vid = match.group(1)
                frequency = match.group(2)
                value = f"{position} - {frequency} - VID({vid})"
            else:
                # If no match found in the string
                value = f"{position} - Data not Parsed"

            embed.add_field(name="", value=value, inline=False)  # Empty name!
    else:
        embed.description = "😴 No active URRV FIR positions found."
    embed.set_footer(text="Updated every minute")
    return embed

# --- Background Tasks ---


@tasks.loop(seconds=CHECK_INTERVAL_SECONDS)
async def monitor_positions():
    """Monitors and updates the announcement."""
    global announcement_message
    if POSITION_ANNOUNCEMENT_CHANNEL_ID:
        channel = bot.get_channel(POSITION_ANNOUNCEMENT_CHANNEL_ID)
        if not channel:
            print("Channel not found!")
            return

        try:
            async with aiohttp.ClientSession() as session:
                current_positions_data = await get_positions_from_site(session)

            embed = await build_position_list_embed(current_positions_data)

            if announcement_message:
                try:
                    await announcement_message.edit(embed=embed)  # Edit embed
                except discord.errors.NotFound:
                    print("Message not found, creating a new one.")
                    announcement_message = await channel.send(embed=embed)
                except discord.errors.Forbidden:
                    print("Missing permissions to edit message.")
                except Exception as e:
                    print(f"Edit Error: {e}")
            else:
                try:
                    # Create the embed
                    announcement_message = await channel.send(embed=embed)
                except discord.errors.Forbidden:
                    print("Missing permissions to send message.")
                except Exception as e:
                    print(f"Send Error: {e}")

        except Exception as e:
            print(f"Task Error: {e}")
    else:
        print("Channel ID not set, skipping.")


@monitor_positions.before_loop
async def before_monitor_positions():
    await bot.wait_until_ready()

# --- Events ---


@bot.event
async def on_ready():
    print(f"Bot {bot.user.name} ready!")
    monitor_positions.start()

# --- Run the Bot ---
bot.run(TOKEN)
