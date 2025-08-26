import os
import discord
from discord.ext import commands, tasks
import aiohttp

# Discord Bot Intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Bot 上線事件
@bot.event
async def on_ready():
    print(f'Bot is ready! Logged in as {bot.user}')
    ping_self.start()  # 啟動自我保活任務

# 傳統指令測試
@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}!")

# 自我保活，每 5 分鐘 ping Railway 網址一次
@tasks.loop(minutes=5)
async def ping_self():
    url = os.getenv("SELF_URL")
    if url:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as resp:
                    print(f"Pinged {url}, status {resp.status}")
            except Exception as e:
                print("Ping error:", e)

# 啟動 Web 伺服器，讓 Railway 可以保持容器活躍
from aiohttp import web

async def handle(request):
    return web.Response(text="Bot is alive!")

app = web.Application()
app.add_routes([web.get("/", handle)])
runner = web.AppRunner(app)

async def start_web():
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8000)))
    await site.start()

bot.loop.create_task(start_web())

# 啟動 Bot
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)