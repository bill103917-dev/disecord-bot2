import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True  # 重要: 讓機器人能讀取訊息內容

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

bot.run("你的TOKEN")