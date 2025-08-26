import os
import discord
from discord.ext import commands

# 設定 Intents
intents = discord.Intents.default()
intents.message_content = True  # 讓 Bot 可以讀訊息內容

bot = commands.Bot(command_prefix="!", intents=intents)

# 上線事件
@bot.event
async def on_ready():
    print(f'Bot is ready! Logged in as {bot.user}')

# 測試訊息
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content == "!ping":
        await message.channel.send("Pong!")

# 確認 Token 是否有載入
TOKEN = os.getenv("DISCORD_TOKEN")
print("Token loaded:", TOKEN is not None)

bot.run(DISCORD_TOKEN)
