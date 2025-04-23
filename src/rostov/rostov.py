import discord
from discord.ext import commands, tasks
import os
import random
import re  # Для регулярных выражений
import asyncio  # Для асинхронных задач (например, мута)
import datetime  # Для работы с датами и временем
import requests
import math
import xml.etree.ElementTree as ET
import aiohttp
from bs4 import BeautifulSoup

# --- Настройки ---
BOT_PREFIX = "/"
WELCOME_CHANNEL_ID = os.getenv('DISCORD_WELCOME_CHANNEL_ID')
ATO_NEWS_CHANNEL_ID = os.getenv('DISCORD_ATO_NEWS_CHANNEL_ID')
ANNOUNCEMENT_EMOJI = "📢"
ROLES_TO_MENTION = ["@Курсанты"]
EXERCISE_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
BOT_COLOR = discord.Color.blue()
FLIGHT_ANNOUNCE_IMAGE_URL = os.getenv('FLIGHT_ANNOUNCE_IMAGE_URL')

# --- Получение токена ---
BOT_TOKEN = os.getenv('DISCORD_TOKEN')

# --- Инициализация бота ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# --- События ---
@bot.event
async def on_ready():
    print(f"Бот {bot.user.name} подключен!")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="за сервером"))

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="Добро пожаловать!",
            description=f"Привет, {member.mention}! Добро пожаловать на сервер {member.guild.name}! Ознакомьтесь с правилами и получите роли.",
            color=BOT_COLOR
        )
        embed.set_thumbnail(url=member.avatar.url)
        await channel.send(embed=embed)

# --- Команда для расчета компонентов ветра ---
@bot.command(name="wind_calculate", help="Рассчитать продольный и боковой компоненты ветра.")
async def wind_calculate(ctx, wind_metar: str, runway_heading: int):
    """Рассчитывает продольный и боковой компоненты ветра.

    Аргументы:
        wind_metar: Направление и скорость ветра из METAR (например, "09005MPS").
        runway_heading: Курс полосы (в градусах).
    """
    try:
        # 1. Извлекаем направление и скорость ветра
        wind_direction = int(wind_metar[:3])  # Первые три символа - направление
        wind_speed = int(wind_metar[3:5])  # Следующие два символа - скорость

        # 2. Переводим углы в радианы
        wind_direction_rad = (wind_direction / 360) * 2 * math.pi
        runway_heading_rad = (runway_heading / 360) * 2 * math.pi

        # 3. Рассчитываем разницу углов
        angle_difference = wind_direction_rad - runway_heading_rad

        # 4. Рассчитываем компоненты ветра
        headwind_component = round(wind_speed * math.cos(angle_difference), 1)  # Продольный (попутный/встречный)
        crosswind_component = round(wind_speed * math.sin(angle_difference), 1)  # Боковой

        # 5. Формируем ответ
        embed = discord.Embed(
            title="💨 Расчет компонентов ветра 💨",
            color=BOT_COLOR,
        )
        embed.add_field(name="Ветер из METAR", value=wind_metar, inline=False)
        embed.add_field(name="Курс полосы", value=f"{runway_heading}°", inline=False)
        embed.add_field(name="Продольный компонент", value=f"{headwind_component} (попутный/встречный)", inline=False)
        embed.add_field(name="Боковой компонент", value=f"{crosswind_component}", inline=False)

        # 6. Отправляем ответ
        await ctx.send(embed=embed)

    except ValueError:
        await ctx.send("Ошибка: Неверный формат данных. Убедитесь, что направление ветра - число от 000 до 360, а курс полосы - целое число.")
    except Exception as e:
        await ctx.send(f"Произошла ошибка при расчете: {e}")

# --- Команды ---
@bot.command(name="hello", description="Приветствует пользователя")
async def hello(ctx):
    embed = discord.Embed(title="**✨ Добро пожаловать! ✨**",
                          description=f"Привет, {ctx.author.mention}! **Рады видеть вас на борту!** 🚀",
                          color=discord.Color.from_rgb(75, 200, 100))
    embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    embed.add_field(name="**Как освоиться?**",
                    value="Прочтите правила и получите роли!", inline=False)
    embed.set_footer(text="Приятного общения!",
                     icon_url=bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="serverinfo", description="Информация о сервере")
async def serverinfo(ctx):
        guild = ctx.guild
        embed = discord.Embed(title=f"**📊 Информация о сервере: {guild.name} 📊**",
                              description=f"Описание: {guild.description or '**Отсутствует**'}\n"
                                          f"Количество участников: **{guild.member_count}**\n"
                                          f"Создан: **{guild.created_at.strftime('%d.%m.%Y %H:%M:%S')}**",
                              color=discord.Color.from_rgb(102, 178, 255))
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        await ctx.send(embed=embed)

@bot.command(name="rules", description="Правила сервера")
async def rules(ctx):
    embed = discord.Embed(title="**📜 Основные правила сервера 📜**",
                          description="1. **Будьте вежливы и уважайте других участников. 🙏**\n"
                                      "2. **Не допускайте спама и флуда в чате. 🚫**\n"
                                      "3. **Избегайте оскорблений и агрессивного поведения. 😠**\n"
                                      "4. **Соблюдайте тематику каналов. 💬**\n"
                                      "5. **Придерживайтесь указаний администрации. 👮**",
                          color=discord.Color.from_rgb(255, 153, 51))
    embed.set_footer(text="Соблюдение правил - залог приятного общения!",
                     icon_url=bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="clear", description="Очищает указанное количество сообщений (только для администраторов).")
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    if 0 < amount <= 100:
        await ctx.channel.purge(limit=amount + 1)
        embed = discord.Embed(
            description=f"**{amount} сообщений успешно удалены. ✅ Чистота - залог порядка!**",
            color=discord.Color.from_rgb(153, 255, 153))
        await ctx.send(embed=embed, delete_after=3)
    else:
        await ctx.send(embed=discord.Embed(
            description="**⚠️ Пожалуйста, укажите число сообщений для удаления в диапазоне от 1 до 100. ⚠️**",
            color=discord.Color.from_rgb(255, 153, 153)))

@bot.command(name="wind_conversion", description="Конвертирует узлы в километры в час.")
async def wind_conversion(ctx, knots: float):
    kmh = knots * 1.852
    embed = discord.Embed(title="**💨 Конвертация скорости ветра 💨**",
                          description=f"{knots} узлов = **{kmh:.2f}** км/ч",
                          color=discord.Color.from_rgb(153, 204, 255))
    embed.set_footer(text="Помните о безопасности полетов!",
                     icon_url=bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar.url)
    await ctx.send(embed=embed)

# --- Команда для отправки сообщений от имени бота ---
@bot.command(name="say", help="Отправить сообщение от имени бота в указанный канал.")
@commands.has_permissions(administrator=True)
async def say(ctx, channel: discord.TextChannel, *, message: str):
        """Отправляет сообщение от имени бота в указанный канал.

        Аргументы:
            channel: Канал, в который нужно отправить сообщение (упоминание канала).
            message: Текст сообщения.
        """
        try:
            embed = discord.Embed(
                description=message,
                color=BOT_COLOR,
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            embed.set_footer(text=f"Отправлено администратором {ctx.author.name}", icon_url=ctx.author.avatar.url)
            await channel.send(embed=embed)
            await ctx.message.delete()  # Удаляем сообщение с командой
        except discord.errors.Forbidden:
            await ctx.send("Ошибка: У меня нет прав на отправку сообщений в этот канал.")
        except Exception as e:
            await ctx.send(f"Произошла ошибка при отправке сообщения: {e}")

# --- Команда для отправки объявлений от имени бота ---
@bot.command(name="announce", help="Отправить объявление от имени бота в указанный канал.")
@commands.has_permissions(administrator=True)
async def announce(ctx, channel: discord.TextChannel, *, message: str):
    """Отправляет объявление от имени бота в указанный канал.

    Аргументы:
        ctx: Контекст команды.
        channel: Канал, в который нужно отправить объявление (упоминание канала).
        message: Текст объявления.
    """
    try:
        # Создаем Embed-сообщение
        embed = discord.Embed(
            title=f"{ANNOUNCEMENT_EMOJI} Объявление",  # Добавляем эмодзи в заголовок
            description=message,
            color=BOT_COLOR,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_footer(text="Объявление от бота")  # Добавляем футер

        # Отправляем сообщение
        await channel.send(embed=embed)

        # Добавляем реакцию к исходному сообщению (опционально)
        await ctx.message.add_reaction("✅")

        # Удаляем сообщение с командой (опционально)
        await ctx.message.delete()

    except discord.errors.Forbidden:
        await ctx.send("Ошибка: У меня нет прав на отправку сообщений в этот канал.")
    except Exception as e:
        await ctx.send(f"Произошла ошибка при отправке сообщения: {e}")

@bot.command(name="flight_announce", help="Создать объявление об учебных полетах с реакциями.")
@commands.has_permissions(administrator=True)
async def flight_announce(ctx, flight_date: str, flight_time: str):
    """Создает объявление об учебных полетах с реакциями.

    Аргументы:
        flight_date: Дата проведения полетов (например, "27.04").
        flight_time: Время проведения полетов (например, "17-19").
    """
    #today = datetime.date.today()
    #days_until_sunday = (6 - today.weekday()) % 7
    #next_sunday = today + datetime.timedelta(days=days_until_sunday)
    #date_string = next_sunday.strftime("%d.%m")
    role_mentions = ' '.join(f'<@&{role.id}>' for role in ctx.guild.roles if role.name in ROLES_TO_MENTION)
    #message_text = f"Учебные полеты {flight_time} URMM IVAO. Сообщите о своем участии, нажав на реакцию с соответствующим номером упражнения. ⬇️"

    channel = bot.get_channel(ATO_NEWS_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="✈️ Учебные полеты 🚀",
            #description=message_text,
            color=BOT_COLOR,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.add_field(name="📅 Дата", value=flight_date, inline=False)
        embed.add_field(name="🕒 Время", value=f"{flight_time} UTC", inline=False)  # Добавляем "UTC" к времени
        embed.add_field(name="📍 Место", value="URMM IVAO", inline=False)
        embed.add_field(name="👥 Участники", value="@Курсанты", inline=False)
        embed.add_field(name="ℹ️ Инструкция", value="Сообщите о своем участии, нажав на реакцию с соответствующим номером упражнения. ⬇️", inline=False)
        embed.set_footer(text="Нажмите на реакцию, чтобы сообщить об участии")
        embed.set_image(url=FLIGHT_ANNOUNCE_IMAGE_URL)  # Добавляем изображение

        message = await channel.send(embed=embed)
        for emoji in EXERCISE_EMOJIS:
            await message.add_reaction(emoji)
        await ctx.message.delete()
    else:
        await ctx.send("Ошибка: Канал #ato-news не найден.")

# --- Модерация ---

@bot.command(name="kick", help="Выгнать участника с сервера.")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    try:
        await member.kick(reason=reason)
        embed = discord.Embed(
            title="Выгнан участник",
            description=f"Участник {member.mention} был выгнан с сервера.",
            color=BOT_COLOR,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        if reason:
            embed.add_field(name="Причина", value=reason, inline=False)
        embed.set_footer(text=f"Модератор: {ctx.author.name}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    except discord.errors.Forbidden:
        await ctx.send("У меня нет прав для выгона этого участника.")
    except discord.errors.NotFound:
        await ctx.send("Участник не найден.")

@bot.command(name="ban", help="Забанить участника на сервере.")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    try:
        await member.ban(reason=reason)
        embed = discord.Embed(
            title="Забанен участник",
            description=f"Участник {member.mention} был забанен на сервере.",
            color=BOT_COLOR,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        if reason:
            embed.add_field(name="Причина", value=reason, inline=False)
        embed.set_footer(text=f"Модератор: {ctx.author.name}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)
    except discord.errors.Forbidden:
        await ctx.send("У меня нет прав для бана этого участника.")
    except discord.errors.NotFound:
        await ctx.send("Участник не найден.")

@bot.command(name="unban", help="Разбанить участника на сервере.")
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int, *, reason=None):
    try:
        user = discord.Object(id=user_id)
        await ctx.guild.unban(user, reason=reason)
        embed = discord.Embed(
            title="Разбанен участник",
            description=f"Участник с ID {user_id} был разбанен на сервере.",
            color=BOT_COLOR,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        if reason:
            embed.add_field(name="Причина", value=reason, inline=False)
        embed.set_footer(text=f"Модератор: {ctx.author.name}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)
    except discord.errors.NotFound:
        await ctx.send("Участник не найден в списке забаненных.")
    except discord.errors.Forbidden:
        await ctx.send("У меня нет прав для разбана участников.")

@bot.command(name="mute", help="Замутить участника на определенное время.")
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, duration: str, *, reason=None):
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not muted_role:
        await ctx.send("Роль 'Muted' не найдена. Пожалуйста, создайте роль с названием 'Muted' и настройте ее права доступа.")
        return

    seconds = parse_duration(duration)
    if seconds is None:
        await ctx.send("Неверный формат продолжительности. Используйте, например, '1m', '5h', '1d'.")
        return

    await member.add_role(muted_role, reason=reason)
    embed = discord.Embed(
        title="Замучен участник",
        description=f"Участник {member.mention} был замучен на {duration}.",
        color=BOT_COLOR,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    if reason:
        embed.add_field(name="Причина", value=reason, inline=False)
    embed.set_footer(text=f"Модератор: {ctx.author.name}", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

    await asyncio.sleep(seconds)

    await member.remove_role(muted_role, reason="Время мута истекло")
    embed = discord.Embed(
        title="Время мута истекло",
        description=f"У участника {member.mention} истек срок мута.",
        color=BOT_COLOR,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    await ctx.send(embed=embed)


@bot.command(name="unmute", help="Снять мут с участника.")
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member, *, reason=None):
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not muted_role:
        await ctx.send("Роль 'Muted' не найдена. Пожалуйста, создайте роль с названием 'Muted' и настройте ее права доступа.")
        return

    await member.remove_role(muted_role, reason=reason)
    embed = discord.Embed(
        title="Снят мут",
        description=f"С участника {member.mention} был снят мут.",
        color=BOT_COLOR,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    if reason:
        embed.add_field(name="Причина", value=reason, inline=False)
    embed.set_footer(text=f"Модератор: {ctx.author.name}", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

    @bot.event
    async def on_message(message):
        # Make sure the bot doesn't respond to itself
        if message.author == bot.user:
            return
    # --- Helper functions ---


def parse_duration(duration: str) -> int:
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    try:
        amount = int(duration[:-1])
        unit = duration[-1].lower()
        if unit in units:
            return amount * units[unit]
        else:
            return None
    except ValueError:
        return None

    # --- Запуск бота ---
bot.run(BOT_TOKEN)
