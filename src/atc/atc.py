import os
import datetime
import discord
from discord.ext import commands, tasks
import aiohttp
from bs4 import BeautifulSoup

# --- Configuration ---
BOT_PREFIX = "/"
POSITION_ANNOUNCEMENT_CHANNEL_ID = int(
    os.getenv("DISCORD_POSITION_ANNOUNCEMENT_CHANNEL_ID", 0)
)
XR_SITE_URL = "https://xr.ivao.aero/"
CHECK_INTERVAL_SECONDS = 60
BOT_COLOR = discord.Color.green()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN not found in environment variables. Please set it.")

# --- Bot Initialization ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# --- Global Variables ---
monitored_positions = {}  # {position: start_time}


# --- Helper Functions ---
async def get_positions_from_site(session: aiohttp.ClientSession) -> list[str]:
    """Retrieves a list of positions starting with 'UR' from the website.

    Args:
        session: The aiohttp client session.

    Returns:
        A list of positions (strings). Returns an empty list on error.
    """
    try:
        async with session.get(XR_SITE_URL, timeout=10) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                table = soup.find("table")
                if not table:
                    print("Table not found on the website!")
                    return []

                positions = []
                for row in table.find_all("tr")[1:]:
                    cells = row.find_all("td")
                    if cells:
                        position = cells[0].text.strip()
                        if position.startswith("UR"):
                            positions.append(position)
                return positions
            else:
                print(f"Error accessing {XR_SITE_URL}: {response.status}")
                return []
    except aiohttp.ClientError as e:
        print(f"Connection error to {XR_SITE_URL}: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while scraping the website: {e}")
        return []


# --- Background Tasks ---
@tasks.loop(seconds=CHECK_INTERVAL_SECONDS)
async def monitor_positions():
    """Checks the website for active positions."""
    channel = bot.get_channel(POSITION_ANNOUNCEMENT_CHANNEL_ID)
    if not channel:
        print(
            f"Announcement channel (ID: {POSITION_ANNOUNCEMENT_CHANNEL_ID})"
            " not found!"
        )
        return

    try:
        async with aiohttp.ClientSession() as session:
            current_positions = await get_positions_from_site(session)

        for position in current_positions:
            if position not in monitored_positions:
                monitored_positions[position] = datetime.datetime.now()
                embed = discord.Embed(
                    title="✅ Position Online!",
                    description=f"Position {position} is now online.",
                    color=BOT_COLOR,
                    timestamp=monitored_positions[position],
                )
                try:
                    await channel.send(embed=embed)
                except discord.errors.Forbidden:
                    print(
                        f"Missing permissions to send messages in channel "
                        f"{channel.id}"
                    )
                except Exception as e:
                    print(
                        f"Error sending message for online position" f" {position}: {e}"
                    )

        ended_positions = []
        for position, start_time in monitored_positions.items():
            if position not in current_positions:
                ended_positions.append(position)
                end_time = datetime.datetime.now()
                duration = end_time - start_time
                hours, remainder = divmod(duration.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)
                duration_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

                embed = discord.Embed(
                    title="❌ Position Offline",
                    description=f"Position {position} has gone offline.",
                    color=BOT_COLOR,
                    timestamp=end_time,
                )
                embed.add_field(name="Online Time", value=duration_str, inline=False)
                try:
                    await channel.send(embed=embed)
                except discord.errors.Forbidden:
                    print(
                        f"Missing permissions to send messages in channel "
                        f"{channel.id}"
                    )
                except Exception as e:
                    print(
                        f"Error sending message for offline position"
                        f" {position}: {e}"
                    )

        for position in ended_positions:
            del monitored_positions[position]

    except Exception as e:
        print(f"An error occurred in the monitor_positions task: {e}")


@monitor_positions.before_loop
async def before_monitor_positions():
    """Waits until the bot is ready before starting the background task."""
    await bot.wait_until_ready()


# --- Events ---
@bot.event
async def on_ready():
    """Prints a message when the bot."""
    print(f"Bot {bot.user.name} ready!")
    monitor_positions.start()


# --- Run the Bot ---
bot.run(TOKEN)
