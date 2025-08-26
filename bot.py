import os
import discord
from discord.ext import commands, tasks
from aiohttp import web
import aiohttp

# -----------------------------
# Web 伺服器（保活用）
# -----------------------------
app = web.Application()

async def handle(request):
    return web.Response(text="Bot is alive!")

app.add_routes([web.get("/", handle)])

async def start_web():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 10000)))
    await site.start()

# -----------------------------
# Discord Bot
# -----------------------------
class MyBot(commands.Bot):
    async def setup_hook(self):
        # 啟動 Web 伺服器
        await start_web()
        # 啟動自我保活任務
        ping_self.start()

intents = discord.Intents.default()
intents.message_content = True

bot = MyBot(command_prefix="!", intents=intents)

# 上線事件
@bot.event
async def on_ready():
    print(f"✅ Bot is ready! Logged in as {bot.user}")

# 指令範例
@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}!")

# 自我保活，每 5 分鐘 ping 自己
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

# 啟動 Bot
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)