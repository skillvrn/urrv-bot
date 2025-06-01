import os
import re
import asyncio
import datetime
import math
import discord
from discord.ext import commands

# --- Настройки ---
BOT_PREFIX = "/"
WELCOME_CHANNEL_ID = int(os.getenv('DISCORD_WELCOME_CHANNEL_ID'))
ATO_NEWS_CHANNEL_ID = int(os.getenv('DISCORD_ATO_NEWS_CHANNEL_ID'))
ANNOUNCEMENT_EMOJI = "📢"
ROLES_TO_MENTION = ["@Курсанты"]
EXERCISE_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
BOT_COLOR = discord.Color.blue()
FLIGHT_ANNOUNCE_IMAGE_URL = (
    "https://media.discordapp.net/"
    "attachments/1274246245967200313/"
    "1361762541436407899/image.png?"
    "ex=67ffefb2&is=67fe9e32&hm="
    "b1152df005c0aa0ca39c0e38bb382e583188be746aa4ebae"
    "2186ea20ad6af777&=&format=webp&quality=lossless"
)

# --- Получение токена ---
BOT_TOKEN = os.getenv("DISCORD_TOKEN")
if not BOT_TOKEN:
    raise ValueError(
        "DISCORD_TOKEN not found in environment variables. Please set it.")

# --- Инициализация бота ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)


# --- События ---
@bot.event
async def on_ready():
    """Called when the bot is connected to Discord."""
    print(f"Бот {bot.user.name} подключен!")
    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name="за сервером")
    await bot.change_presence(activity=activity)


@bot.event
async def on_member_join(member: discord.Member):
    """Welcomes new members to the server."""
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="Добро пожаловать!",
            description=(
                f"Привет, {member.mention}! Добро пожаловать на сервер "
                f"{member.guild.name}! Ознакомьтесь с правилами и "
                f"получите роли."
            ),
            color=BOT_COLOR,
        )
        embed.set_thumbnail(url=member.avatar.url)
        await channel.send(embed=embed)
    else:
        print(
            f"WARNING: Welcome channel (ID: {WELCOME_CHANNEL_ID}) not found.")


# --- Команды ---
@bot.command(name="hello", description="Приветствует пользователя")
async def hello(ctx: commands.Context):
    """Greets the user with a welcoming message."""
    embed = discord.Embed(
        title="✨ Добро пожаловать! ✨",
        description=(
            f"Привет, {
                ctx.author.mention}! **Рады видеть вас на борту!** 🚀"
        ),
        color=discord.Color.from_rgb(75, 200, 100),
    )
    embed.set_thumbnail(
        url=(
            ctx.author.avatar.url
            if ctx.author.avatar
            else ctx.author.default_avatar.url
        )
    )
    embed.add_field(
        name="**Как освоиться?**",
        value="Прочтите правила и получите роли!",
        inline=False,
    )
    embed.set_footer(
        text="Приятного общения!",
        icon_url=(
            bot.user.avatar.url
            if bot.user.avatar
            else bot.user.default_avatar.url
        ),
    )
    await ctx.send(embed=embed)


@bot.command(name="serverinfo", description="Информация о сервере")
async def serverinfo(ctx: commands.Context):
    """Displays information about the server."""
    guild = ctx.guild
    embed = discord.Embed(
        title=f"📊 Информация о сервере: {guild.name} 📊",
        description=(
            f"Описание: {guild.description or '**Отсутствует**'}\n"
            f"Количество участников: **{guild.member_count}**\n"
            f"Создан: {guild.created_at.strftime('%d.%m.%Y %H:%M:%S')}"
        ),
        color=discord.Color.from_rgb(102, 178, 255),
    )
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    await ctx.send(embed=embed)


@bot.command(name="rules", description="Правила сервера")
async def rules(ctx: commands.Context):
    """Displays the server rules."""
    embed = discord.Embed(
        title="📜 Основные правила сервера 📜",
        description=(
            "1. **Будьте вежливы и уважайте других участников. 🙏**\n"
            "2. **Не допускайте спама и флуда в чате. 🚫**\n"
            "3. **Избегайте оскорблений и агрессивного поведения. 😠**\n"
            "4. **Соблюдайте тематику каналов. 💬**\n"
            "5. **Придерживайтесь указаний администрации. 👮**"
        ),
        color=discord.Color.from_rgb(255, 153, 51),
    )
    embed.set_footer(
        text="Соблюдение правил-залог приятного общения!",
        icon_url=(
            bot.user.avatar.url
            if bot.user.avatar
            else bot.user.default_avatar.url),
    )
    await ctx.send(embed=embed)


@bot.command(
    name="clear",
    description="Очищает указанное количество сообщений.",
)
@commands.has_permissions(manage_messages=True)
async def clear(ctx: commands.Context, amount: int):
    """Deletes a specified number of messages."""
    if 0 < amount <= 100:
        try:
            await ctx.channel.purge(limit=amount + 1)
            embed = discord.Embed(
                description=(
                    f"**{amount} сообщений успешно удалены. ✅ Чистота - "
                    "залог порядка!**"
                ),
                color=discord.Color.from_rgb(153, 255, 153),
            )
            await ctx.send(embed=embed, delete_after=3)
        except discord.errors.Forbidden:
            await ctx.send("У меня нет прав.")
        except Exception as e:
            await ctx.send(f"Произошла ошибка при удалении сообщений: {e}")
    else:
        embed = discord.Embed(
            description=(
                "**⚠️ Пожалуйста, укажите число сообщений для удаления в "
                "диапазоне от 1 до 100. ⚠️**"
            ),
            color=discord.Color.from_rgb(255, 153, 153),
        )
        await ctx.send(embed=embed)


@bot.command(name="wind_conversion",
             description="Конвертирует узлы в километры в час.")
async def wind_conversion(ctx: commands.Context, knots: float):
    """Converts knots to kilometers per hour."""
    kmh = knots * 1.852
    embed = discord.Embed(
        title="💨 Конвертация скорости ветра 💨",
        description=f"{knots} узлов = **{kmh:.2f}** км/ч",
        color=discord.Color.from_rgb(153, 204, 255),
    )
    embed.set_footer(
        text="Помните о безопасности полетов!",
        icon_url=(
            bot.user.avatar.url
            if bot.user.avatar
            else bot.user.default_avatar.url
        ),
    )
    await ctx.send(embed=embed)


@bot.command(name="wind_calculate",
             help="Рассчитать продольный и боковой компоненты ветра.")
async def wind_calculate(
        ctx: commands.Context,
        wind_metar: str,
        runway_heading: int):
    """Рассчитывает продольный и боковой компоненты ветра.

    Args:
        ctx: The command context.
        wind_metar: Направление и скорость ветра из METAR
                    (например, "09005MPS").
        runway_heading: Курс полосы (в градусах).
    """
    try:
        wind_direction = int(wind_metar[:3])
        wind_speed = int(wind_metar[3:5])

        wind_direction_rad = math.radians(wind_direction)
        runway_heading_rad = math.radians(runway_heading)

        angle_difference = wind_direction_rad - runway_heading_rad

        headwind_component = round(wind_speed * math.cos(angle_difference), 1)
        crosswind_component = round(wind_speed * math.sin(angle_difference), 1)

        embed = discord.Embed(
            title="💨 Расчет компонентов ветра 💨",
            color=BOT_COLOR,
        )
        embed.add_field(name="Ветер из METAR", value=wind_metar, inline=False)
        embed.add_field(
            name="Курс полосы",
            value=f"{runway_heading}°",
            inline=False)
        embed.add_field(
            name="Продольный компонент",
            value=f"{headwind_component} (попутный/встречный)",
            inline=False,
        )
        embed.add_field(
            name="Боковой компонент",
            value=f"{crosswind_component}",
            inline=False)

        await ctx.send(embed=embed)

    except ValueError:
        await ctx.send(
            "Ошибка: Неверный формат данных. - "
            "число от 000 до 360, а курс полосы - целое число."
        )
    except Exception as e:
        await ctx.send(f"Произошла ошибка при расчете: {e}")


@bot.command(name="say",
             help="Отправить сообщение от имени бота в указанный канал.")
@commands.has_permissions(administrator=True)
async def say(
        ctx: commands.Context,
        channel: discord.TextChannel,
        *,
        message: str):
    """Отправляет сообщение от имени бота в указанный канал.

    Args:
        ctx: Контекст команды.
        channel: Канал, в который нужно отправить сообщение.
        message: Текст сообщения.
    """
    try:
        embed = discord.Embed(
            description=message,
            color=BOT_COLOR,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        embed.set_footer(
            text=f"Отправлено администратором {ctx.author.name}",
            icon_url=ctx.author.avatar.url,
        )
        await channel.send(embed=embed)
        await ctx.message.delete()
    except discord.errors.Forbidden:
        await ctx.send("У меня нет прав на отправку сообщений в этот канал.")
    except Exception as e:
        await ctx.send(f"Произошла ошибка при отправке сообщения: {e}")


@bot.command(name="announce",
             help="Отправить объявление от имени бота в указанный канал.")
@commands.has_permissions(administrator=True)
async def announce(
    ctx: commands.Context, channel: discord.TextChannel, *, message: str
):
    """Отправляет объявление от имени бота в указанный канал.

    Args:
        ctx: Контекст команды.
        channel: Канал, в который нужно отправить объявление.
        message: Текст сообщения.
    """
    try:
        embed = discord.Embed(
            title=f"{ANNOUNCEMENT_EMOJI} Объявление",
            description=message,
            color=BOT_COLOR,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        embed.set_footer(text="Объявление от бота")

        await channel.send(embed=embed)

        await ctx.message.add_reaction("✅")

        await ctx.message.delete()

    except discord.errors.Forbidden:
        await ctx.send("У меня нет прав на отправку сообщений в этот канал.")
    except Exception as e:
        await ctx.send(f"Произошла ошибка при отправке сообщения: {e}")


@bot.command(name="flight_announce",
             help="Создать объявление об учебных полетах с реакциями.")
@commands.has_permissions(administrator=True)
async def flight_announce(
        ctx: commands.Context,
        flight_date: str,
        flight_time: str):
    """Creates a flight announcement with reactions."""
    channel = bot.get_channel(ATO_NEWS_CHANNEL_ID)
    if not channel:
        await ctx.send("Ошибка: Канал #ato-news не найден.")
        return

    try:
        embed = discord.Embed(
            title="✈️ Учебные полеты 🚀",
            color=BOT_COLOR,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        embed.add_field(name="📅 Дата", value=flight_date, inline=False)
        embed.add_field(
            name="🕒 Время",
            value=f"{flight_time} UTC",
            inline=False)
        embed.add_field(name="📍 Место", value="URMM IVAO", inline=False)
        embed.add_field(
            name="👥 Участники", value=" ".join(ROLES_TO_MENTION), inline=False
        )
        embed.add_field(
            name="ℹ️ Инструкция",
            value=(
                "Сообщите о своем участии, нажав на реакцию с "
                "соответствующим номером упражнения. ⬇️"
            ),
            inline=False,
        )
        embed.set_footer(text="Нажмите на реакцию, чтобы сообщить об участии")
        embed.set_image(url=FLIGHT_ANNOUNCE_IMAGE_URL)

        message = await channel.send(embed=embed)
        for emoji in EXERCISE_EMOJIS:
            await message.add_reaction(emoji)
        await ctx.message.delete()

    except discord.errors.Forbidden:
        await ctx.send("У меня нет прав для отправки сообщений в этот канал.")
    except Exception as e:
        await ctx.send(f"Произошла ошибка при создании объявления: {e}")


# --- Модерация ---
@bot.command(name="kick", help="Выгнать участника с сервера.")
@commands.has_permissions(kick_members=True)
async def kick(ctx: commands.Context, member: discord.Member, *, reason=None):
    """Kicks a member from the server."""
    try:
        await member.kick(reason=reason)
        embed = discord.Embed(
            title="Выгнан участник",
            description=f"Участник {member.mention} был выгнан с сервера.",
            color=BOT_COLOR,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        if reason:
            embed.add_field(name="Причина", value=reason, inline=False)
        embed.set_footer(
            text=f"Модератор: {ctx.author.name}",
            icon_url=ctx.author.avatar.url,
        )
        await ctx.send(embed=embed)

    except discord.errors.Forbidden:
        await ctx.send("У меня нет прав для выгона этого участника.")
    except discord.errors.NotFound:
        await ctx.send("Участник не найден.")
    except Exception as e:
        await ctx.send(f"Произошла ошибка при кике: {e}")


@bot.command(name="ban", help="Забанить участника на сервере.")
@commands.has_permissions(ban_members=True)
async def ban(ctx: commands.Context, member: discord.Member, *, reason=None):
    """Bans a member from the server."""
    try:
        await member.ban(reason=reason)
        embed = discord.Embed(
            title="Забанен участник",
            description=f"Участник {member.mention} был забанен с сервера.",
            color=BOT_COLOR,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        if reason:
            embed.add_field(name="Причина", value=reason, inline=False)
        embed.set_footer(
            text=f"Модератор: {ctx.author.name}",
            icon_url=ctx.author.avatar.url,
        )
        await ctx.send(embed=embed)
    except discord.errors.Forbidden:
        await ctx.send("У меня нет прав для бана этого участника.")
    except discord.errors.NotFound:
        await ctx.send("Участник не найден.")
    except Exception as e:
        await ctx.send(f"Произошла ошибка при бане: {e}")


@bot.command(name="unban", help="Разбанить участника на сервере.")
@commands.has_permissions(ban_members=True)
async def unban(ctx: commands.Context, user_id: int, *, reason=None):
    """Unbans a user from the server."""
    try:
        user = discord.Object(id=user_id)
        await ctx.guild.unban(user, reason=reason)
        embed = discord.Embed(
            title="Разбанен участник",
            description=f"Участник с ID {user_id} был разбанен на сервере.",
            color=BOT_COLOR,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        if reason:
            embed.add_field(name="Причина", value=reason, inline=False)
        embed.set_footer(
            text=f"Модератор: {ctx.author.name}",
            icon_url=ctx.author.avatar.url,
        )
        await ctx.send(embed=embed)
    except discord.errors.Forbidden:
        await ctx.send("У меня нет прав для разбана участников.")
    except discord.errors.NotFound:
        await ctx.send("Участник не найден в списке забаненных.")
    except Exception as e:
        await ctx.send(f"Произошла ошибка при разбане: {e}")


@bot.command(name="mute", help="Замутить участника на определенное время.")
@commands.has_permissions(manage_roles=True)
async def mute(
        ctx: commands.Context,
        member: discord.Member,
        duration: str,
        *,
        reason=None):
    """Mutes a member for a specified duration."""
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not muted_role:
        await ctx.send(
            "Роль 'Muted' не найдена. Пожалуйста, создайте роль с названием "
            "'Muted' и настройте ее права доступа."
        )
        return

    seconds = parse_duration(duration)
    if seconds is None:
        await ctx.send(
            "Неверный формат продолжительности. Используйте, например, '1m', "
            "'5h', '1d'."
        )
        return

    try:
        await member.add_role(muted_role, reason=reason)
        embed = discord.Embed(
            title="Замучен участник",
            description=f"Участник {
                member.mention} был замучен на {duration}.",
            color=BOT_COLOR,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        if reason:
            embed.add_field(name="Причина", value=reason, inline=False)
        embed.set_footer(
            text=f"Модератор: {ctx.author.name}",
            icon_url=ctx.author.avatar.url,
        )
        await ctx.send(embed=embed)

        await asyncio.sleep(seconds)

        await member.remove_role(muted_role, reason="Время мута истекло")
        embed = discord.Embed(
            title="Время мута истекло",
            description=f"У участника {member.mention} истек срок мута.",
            color=BOT_COLOR,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        await ctx.send(embed=embed)
    except discord.errors.Forbidden:
        await ctx.send("У меня нет прав")
    except Exception as e:
        await ctx.send(f"Произошла ошибка при муте: {e}")


@bot.command(name="unmute", help="Снять мут с участника.")
@commands.has_permissions(manage_roles=True)
async def unmute(
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason=None):
    """Removes the mute from a member."""
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not muted_role:
        await ctx.send(
            "Роль 'Muted' не найдена. Пожалуйста, создайте роль с названием "
            "'Muted' и настройте ее права доступа."
        )
        return

    try:
        await member.remove_role(muted_role, reason=reason)
        embed = discord.Embed(
            title="Снят мут",
            description=f"С участника {member.mention} был снят мут.",
            color=BOT_COLOR,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        if reason:
            embed.add_field(name="Причина", value=reason, inline=False)
        embed.set_footer(
            text=f"Модератор: {ctx.author.name}",
            icon_url=ctx.author.avatar.url,
        )
        await ctx.send(embed=embed)
    except discord.errors.Forbidden:
        await ctx.send("У меня нет прав")
    except Exception as e:
        await ctx.send(f"Произошла ошибка при снятии мута: {e}")


@bot.event
async def on_message(message: discord.Message):
    """Handles messages, important for command processing."""
    if message.author == bot.user:
        return
    await bot.process_commands(message)


# --- Helper functions ---
def parse_duration(duration: str) -> int | None:
    """Parses a duration string (e.g., '1m', '5h') into seconds."""
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    match = re.match(r"^(\d+)([smhd])$", duration)
    if match:
        amount, unit = int(match.group(1)), match.group(2)
        return amount * units[unit]
    return None


# --- Запуск бота ---
bot.run(BOT_TOKEN)
