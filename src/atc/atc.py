import os
import datetime
import discord
from discord.ext import commands, tasks
import aiohttp
from bs4 import BeautifulSoup
import re

# --- Config ---
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID') or 0)
XR_URL = "https://xr.ivao.aero/"
CHECK_INTERVAL = 300

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Data ---
current_positions = set()


# --- Functions ---
async def get_positions():
    """Get positions from IVAO site."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(XR_URL, timeout=10) as resp:
                if resp.status != 200:
                    return []

                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")
                table = soup.find("table")
                if not table:
                    return []

                positions = []
                for row in table.find_all("tr")[1:]:
                    cells = row.find_all("td")
                    if cells and len(cells) >= 2:
                        pos = cells[0].text.strip()
                        if pos.startswith("UR"):
                            data = cells[1].text.strip()
                            positions.append(
                                {"position": pos, "data": data}
                            )
                return positions
    except Exception:
        return []


def get_info(data):
    """Extract VID and frequency."""
    match = re.search(r"(\d{6}).*?(\d+\.\d+)Mhz", data)
    if match:
        return {"vid": match.group(1), "frequency": match.group(2)}
    return {"vid": "Unknown", "frequency": "Unknown"}


async def send_alert(channel, pos_name, info, is_open=True):
    """Send position alert."""
    title = "🚨 NEW POSITION OPENED!" if is_open else "🔴 POSITION CLOSED"
    color = discord.Color.green() if is_open else discord.Color.red()

    embed = discord.Embed(
        title=title,
        color=color,
        timestamp=datetime.datetime.now()
    )

    if is_open:
        embed.add_field(
            name="📍 Position",
            value=f"```{pos_name}```",
            inline=False
        )
        embed.add_field(
            name="📡 Frequency",
            value=f"```{info['frequency']}```",
            inline=True
        )
        embed.add_field(
            name="👨‍✈️ Controller VID",
            value=f"```{info['vid']}```",
            inline=True
        )
        embed.add_field(
            name="⏰ Opened",
            value=f"<t:{int(datetime.datetime.now().timestamp())}:T>",
            inline=False
        )
    else:
        embed.description = f"Position **{pos_name}** is no longer active."

    # Add footer
    embed.set_footer(text="URRV FIR Positions Monitoring System")

    await channel.send(embed=embed)


# --- Task ---
@tasks.loop(seconds=CHECK_INTERVAL)
async def check_positions():
    """Check for position changes."""
    if not CHANNEL_ID:
        return

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    positions_data = await get_positions()
    new_positions = {p["position"] for p in positions_data}

    # Find changes
    opened = new_positions - current_positions
    closed = current_positions - new_positions

    # Send alerts
    for pos in opened:
        pos_data = next(
            (p for p in positions_data if p["position"] == pos),
            None
        )
        if pos_data:
            info = get_info(pos_data["data"])
            await send_alert(channel, pos, info, is_open=True)

    for pos in closed:
        await send_alert(channel, pos, {}, is_open=False)

    # Update current positions
    current_positions.clear()
    current_positions.update(new_positions)


@check_positions.before_loop
async def before_check():
    await bot.wait_until_ready()


# --- Events ---
@bot.event
async def on_ready():
    print(f"Bot {bot.user.name} online")
    check_positions.start()


# --- Run ---
if __name__ == "__main__":
    bot.run(TOKEN)
