import discord
from discord.ext import commands, tasks
import os
import random
import re  # Для регулярных выражений
import asyncio  # Для асинхронных задач (например, мута)
import datetime  # Для работы с датами и временем
import requests
import xml.etree.ElementTree as ET

# --- Настройки ---
BOT_PREFIX = "!"
ANNOUNCEMENT_CHANNEL_ID = os.getenv('DISCORD_ANNOUNCEMENT_CHANNEL_ID')
WELCOME_CHANNEL_ID = os.getenv('DISCORD_WELCOME_CHANNEL_ID')
ATO_NEWS_CHANNEL_ID = os.getenv('DISCORD_ATO_NEWS_CHANNEL_ID')
ROLES_TO_MENTION = ["Курсанты"]
EXERCISE_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
BOT_COLOR = discord.Color.blue()
FLIGHT_ANNOUNCE_IMAGE_URL = "https://media.discordapp.net/attachments/1274246245967200313/1361762541436407899/image.png?ex=67ffefb2&is=67fe9e32&hm=b1152df005c0aa0ca39c0e38bb382e583188be746aa4ebae2186ea20ad6af777&=&format=webp&quality=lossless"

# --- Получение токена ---
BOT_TOKEN = os.getenv('DISCORD_TOKEN')
if BOT_TOKEN == "YOUR_BOT_TOKEN":
    print("WARNING: Используется токен по умолчанию! Пожалуйста, замените его на реальный токен.")

# --- Инициализация бота ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# --- События ---
@bot.event
async def on_ready():
    print(f"Бот {bot.user.name} подключен!")
    print(f"ANNOUNCEMENT_CHANNEL_ID: {ANNOUNCEMENT_CHANNEL_ID}")
    print(f"WELCOME_CHANNEL_ID: {WELCOME_CHANNEL_ID}")
    print(f"ATO_NEWS_CHANNEL_ID: {ATO_NEWS_CHANNEL_ID}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="за сервером"))
    check_and_send_weekly_flight_announcement.start()

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

    @bot.command(name="say", description="Отправить сообщение в канал от имени бота (только для администраторов)")
    @commands.has_permissions(administrator=True)
    async def say(ctx, channel: discord.TextChannel, *, message: str):
        """
        Отправляет сообщение в указанный канал от имени бота.
        """
        try:
            await channel.send(message)
            embed = discord.Embed(description=f"**✅ Сообщение отправлено в {channel.mention}!**",
                                  color=discord.Color.green())
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(
                description=f"**🚫 Ошибка: Недостаточно прав для отправки сообщения в {channel.mention}!**",
                color=discord.Color.red())
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")
            embed = discord.Embed(
                description="**❌ Произошла ошибка при отправке сообщения. Обратитесь к разработчику бота!**",
                color=discord.Color.red())
            await ctx.send(embed=embed)

@bot.command(name="announce", help="Отправить объявление от имени бота.")
@commands.has_permissions(administrator=True)
async def announce(ctx, *, message):
    channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="Объявление",
            description=message,
            color=BOT_COLOR,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_footer(text=f"Отправлено администратором {ctx.author.name}", icon_url=ctx.author.avatar.url)
        await channel.send(embed=embed)
        await ctx.message.delete()
    else:
        await ctx.send("Ошибка: Канал объявлений не найден.")

@bot.command(name="flight_announce", help="Создать объявление об учебных полетах с реакциями.")
@commands.has_permissions(administrator=True)
async def flight_announce(ctx):
    today = datetime.date.today()
    days_until_sunday = (6 - today.weekday()) % 7
    next_sunday = today + datetime.timedelta(days=days_until_sunday)
    date_string = next_sunday.strftime("%d.%m")
    role_mentions = ' '.join(f'<@&{role.id}>' for role in ctx.guild.roles if role.name in ROLES_TO_MENTION)
    message_text = f"Учебные полеты ({date_string}) 17-19 UTC URMM IVAO. Сообщите о своем участии, нажав на реакцию с соответствующим номером упражнения. ⬇️"

    channel = bot.get_channel(ATO_NEWS_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="Учебные полеты",
            description=message_text,
            color=BOT_COLOR,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.add_field(name="Участники", value=role_mentions, inline=False)
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

# --- Фоновые задачи ---
@tasks.loop(hours=24)
async def check_and_send_weekly_flight_announcement():
    now = datetime.datetime.now()
    if now.weekday() == 2 and now.hour == 12 and now.minute == 0:
        channel = bot.get_channel(ATO_NEWS_CHANNEL_ID) #ATO NEWS CHANNEL
        if channel:
            today = datetime.date.today()
            days_until_sunday = (6 - today.weekday()) % 7
            next_sunday = today + datetime.timedelta(days=days_until_sunday)
            date_string = next_sunday.strftime("%d.%m")
            role_mentions = ' '.join(f'<@&{role.id}>' for role in ctx.guild.roles if role.name in ROLES_TO_MENTION)
            message_text = f"Учебные полеты ({date_string}) 17-19 UTC URMM IVAO. Сообщите о своем участии, нажав на реакцию с соответствующим номером упражнения. ⬇️"

            embed = discord.Embed(
                title="Учебные полеты",
                description=message_text,
                color=BOT_COLOR,
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            embed.add_field(name="Участники", value=role_mentions, inline=False)
            embed.set_footer(text="Нажмите на реакцию, чтобы сообщить об участии")
            embed.set_image(url=FLIGHT_ANNOUNCE_IMAGE_URL) # Добавляем изображение
            message = await channel.send(embed=embed)

            for emoji in EXERCISE_EMOJIS:
                await message.add_reaction(emoji)
            print("Объявление об учебных полетах отправлено.")
        else:
            print("Ошибка: Канал объявлений не найден.")

@check_and_send_weekly_flight_announcement.before_loop
async def before_check_and_send():
    await bot.wait_until_ready()

# --- Запуск бота ---
bot.run(BOT_TOKEN)
