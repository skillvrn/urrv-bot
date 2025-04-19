import discord
from discord.ext import commands
import requests
import re
import xml.etree.ElementTree as ET
import os

# Create the bot instance (assuming you've already done this)
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Regular expression for valid ICAO code (4 letters)
ICAO_REGEX = r"^[A-Z]{4}$"

# Command to get METAR and TAF data
@bot.command(name="weather", description="Получить METAR и TAF данные для указанного ICAO аэропорта с metartaf.ru")
async def weather_command(ctx, icao: str):
    """
    Получает METAR и TAF данные для указанного ICAO аэропорта с metartaf.ru.
    """

    # Validate ICAO
    if re.match(ICAO_REGEX, icao.upper()):
        icao = icao.upper()  # Convert to uppercase for API

        try:
            url = f"http://metartaf.ru/{icao}.xml"  # API URL
            response = requests.get(url)
            response.raise_for_status()  # Raises HTTPError for bad responses

            xml_content = response.text  # XML DATA

            # Parse the XML
            root = ET.fromstring(xml_content)

            # Extract data
            metar = root.find('metar').text if root.find('metar') is not None else None
            taf = root.find('taf').text if root.find('taf') is not None else None

            # Format the output (only include fields if they exist)
            formatted_message = f"**Weather Data for {icao}:**\n```\n"

            if metar:
                formatted_message += f"METAR: {metar}\n"

            if taf:
                formatted_message += f"TAF: {taf}\n"

            formatted_message += "```"

            # Only send if there is actually content
            if metar or taf:
                await ctx.send(formatted_message)
            else:
                await ctx.send(f"No METAR or TAF data found for {icao}.") #If it's all null

        except requests.exceptions.RequestException as e:
            await ctx.send(f"Ошибка при получении данных для {icao}, возможно Вы ввели неверный ICAO")
        except Exception as e:
            await ctx.send(f"Произошла непредвиденная ошибка для {icao}: {e}")

    else:
        await ctx.send("Неверный формат ICAO кода. Пожалуйста, используйте 4-буквенный код (например, UUDD).")

# Assuming you have a token
bot.run(os.getenv('DISCORD_TOKEN'))
