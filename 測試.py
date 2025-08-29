from discord.ext import commands
from discord import app_commands
import discord
import asyncio
from aiohttp import web
import random
import os

# =========================
# 保活 server
# =========================
async def keep_alive():
    async def handle(request):
        return web.Response(text="Bot is running!")
    app = web.Application()
    app.add_routes([web.get("/", handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("✅ HTTP server running on port 8080")

# =========================
# Cog 定義
# =========================
class UtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="測試 Bot 是否在線")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message("🏓 Pong!", ephemeral=True)

class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rps_choices = {"剪刀":"✂️","石頭":"🪨","布":"📄"}

    @app_commands.command(name="rps", description="玩剪刀石頭布")
    @app_commands.describe(choice="剪刀/石頭/布")
    async def rps(self, interaction: discord.Interaction, choice: str):
        if choice not in self.rps_choices:
            await interaction.response.send_message("❌ 請輸入 剪刀/石頭/布", ephemeral=True)
            return
        bot_choice = random.choice(list(self.rps_choices.keys()))
        if choice == bot_choice:
            result = "平手 🤝"
        elif (choice=="剪刀" and bot_choice=="布") or (choice=="石頭" and bot_choice=="剪刀") or (choice=="布" and bot_choice=="石頭"):
            result = "你贏了 🎉"
        else:
            result = "你輸了 😢"
        await interaction.response.send_message(
            f"你出 {self.rps_choices[choice]} ({choice})\n我出 {self.rps_choices[bot_choice]} ({bot_choice})\n結果：{result}"
        )

    @app_commands.command(name="draw", description="隨機抽籤")
    @app_commands.describe(options="多個選項，用逗號或空格分隔")
    async def draw(self, interaction: discord.Interaction, options: str):
        if "," in options:
            items = [o.strip() for o in options.split(",") if o.strip()]
        else:
            items = [o.strip() for o in options.split() if o.strip()]
        if len(items) < 2:
            await interaction.response.send_message("❌ 請至少輸入兩個選項", ephemeral=True)
            return
        winner = random.choice(items)
        await interaction.response.send_message(f"🎉 抽籤結果：**{winner}**")

# =========================
# Cog 載入函數
# =========================
async def setup_cogs(bot):
    await bot.add_cog(UtilityCog(bot))
    await bot.add_cog(FunCog(bot))

# =========================
# 啟動 Bot
# =========================
TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ 已登入：{bot.user} (ID: {bot.user.id})")

async def main():
    await setup_cogs(bot)
    asyncio.create_task(keep_alive())  # 非阻塞保活
    await bot.start(TOKEN)

loop = asyncio.get_event_loop()
loop.create_task(main())
loop.run_forever()