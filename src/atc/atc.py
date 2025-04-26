import discord
from discord.ext import commands, tasks
import aiohttp
from bs4 import BeautifulSoup
import asyncio
import datetime
import os

# --- Настройки ---
BOT_PREFIX = "/"
POSITION_ANNOUNCEMENT_CHANNEL_ID = os.getenv('DISCORD_POSITION_ANNOUNCEMENT_CHANNEL_ID')
XR_SITE_URL = os.getenv('XR_SITE_URL')
CHECK_INTERVAL_SECONDS = 120  # Как часто проверять сайт
BOT_COLOR = discord.Color.green()

# --- Получение токена ---
TOKEN = os.environ.get("DISCORD_TOKEN")

# --- Инициализация бота ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# --- Глобальные переменные ---
monitored_positions = {}  # {position: start_time}

async def get_positions_from_site(session):
    """Извлекает список позиций, начинающихся с 'UR', с сайта."""
    try:
        async with session.get(XR_SITE_URL) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Ищем таблицу
                table = soup.find('table')
                if not table:
                    print("Таблица не найдена!")
                    return []

                positions = []
                for row in table.find_all('tr')[1:]:
                    cells = row.find_all('td')
                    if cells:
                        position = cells[0].text.strip()
                        if position.startswith("UR"):
                            positions.append(position)
                return positions
            else:
                print(f"Ошибка при доступе к сайту {XR_SITE_URL}: {response.status}")
                return []
    except aiohttp.ClientError as e:
        print(f"Ошибка подключения к {XR_SITE_URL}: {e}")
        return []

# --- Фоновые задачи ---
@tasks.loop(seconds=CHECK_INTERVAL_SECONDS)
async def monitor_positions():
    """Проверяет сайт на наличие позиций и отправляет уведомления."""
    channel = bot.get_channel(POSITION_ANNOUNCEMENT_CHANNEL_ID)
    if not channel:
        print("Канал для объявлений не найден!")
        return

    async with aiohttp.ClientSession() as session:
        current_positions = await get_positions_from_site(session)

    # 1. Новые позиции
    for position in current_positions:
        if position not in monitored_positions:
            monitored_positions[position] = datetime.datetime.now()
            embed = discord.Embed(
                title="✅ Позиция онлайн!",
                description=f"Позиция {position} начала работу.",
                color=BOT_COLOR,
                timestamp=monitored_positions[position]
            )
            try:
                await channel.send(embed=embed)
            except Exception as e:
                print(f"Ошибка при отправке сообщения: {e}")

    # 2. Завершение работы позиций
    ended_positions = []
    for position, start_time in monitored_positions.items():
        if position not in current_positions:
            ended_positions.append(position)
            end_time = datetime.datetime.now()
            duration = end_time - start_time
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            duration_str = f"{int(hours)}ч {int(minutes)}м {int(seconds)}с"

            embed = discord.Embed(
                title="❌ Позиция завершила работу",
                description=f"Позиция {position} закончила работу.",
                color=BOT_COLOR,
                timestamp=end_time
            )
            embed.add_field(name="Время работы", value=duration_str, inline=False)
            try:
                await channel.send(embed=embed)
            except Exception as e:
                print(f"Ошибка при отправке сообщения: {e}")

    # Очистка
    for position in ended_positions:
        del monitored_positions[position]

@monitor_positions.before_loop
async def before_monitor_positions():
    await bot.wait_until_ready()

# --- События ---
@bot.event
async def on_ready():
    print(f"Бот {bot.user.name} готов!")
    if POSITION_ANNOUNCEMENT_CHANNEL_ID:
        print(f"ID канала для объявлений: {POSITION_ANNOUNCEMENT_CHANNEL_ID}", flush=True)
    else:
        print("⚠️ DISCORD_POSITION_ANNOUNCEMENT_CHANNEL_ID не установлен!", flush=True)
    monitor_positions.start()

# --- Запуск бота ---
bot.run(TOKEN)
