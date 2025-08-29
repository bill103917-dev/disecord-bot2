import os
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from aiohttp import web
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import random
from flask import Flask
import threading
# =========================
# 🔧 輔助函數
# =========================
def parse_time(timestr: str) -> int:
    units = {"s": 1, "m": 60, "h": 3600}
    num = ""
    total = 0
    for char in timestr:
        if char.isdigit():
            num += char
        elif char in units:
            if not num:
                raise ValueError("時間格式錯誤，缺少數字")
            total += int(num) * units[char]
            num = ""
        else:
            raise ValueError(f"無效的時間單位: {char}")
    if num:
        total += int(num)
    if total <= 0:
        raise ValueError("時間必須大於 0 秒")
    return total

def format_duration(seconds: int) -> str:
    h, m, s = seconds // 3600, (seconds % 3600) // 60, seconds % 60
    parts = []
    if h: parts.append(f"{h} 小時")
    if m: parts.append(f"{m} 分鐘")
    if s: parts.append(f"{s} 秒")
    return " ".join(parts) if parts else "0 秒"

COUNTRY_TIMEZONES = {
    "台灣": "Asia/Taipei",
    "日本": "Asia/Tokyo",
    "美國東岸": "America/New_York",
    "美國西岸": "America/Los_Angeles",
    "英國": "Europe/London",
    "德國": "Europe/Berlin",
    "澳洲": "Australia/Sydney"
}

OWNER_ID = 1238436456041676853
SPECIAL_USER_IDS = [OWNER_ID]

PORT = int(os.environ.get("PORT", 8080))
app.run(host='0.0.0.0', port=PORT)

from aiohttp import web
import asyncio

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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# =========================
# 📌 UtilityCog
# =========================
class UtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="測試 Bot 是否在線")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message("🏓 Pong!", ephemeral=True)

    @app_commands.command(name="hello", description="打招呼")
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"👋 哈囉 {interaction.user.mention}!", ephemeral=True)

    @app_commands.command(name="timer", description="設定計時器")
    async def timer(self, interaction: discord.Interaction, timestr: str):
        try:
            total_seconds = parse_time(timestr)
        except ValueError as e:
            await interaction.response.send_message(f"❌ {e}", ephemeral=True)
            return
        await interaction.response.send_message(f"⏳ 計時器開始：{timestr}", ephemeral=True)
        async def task():
            await asyncio.sleep(total_seconds)
            await interaction.channel.send(f"⏰ {interaction.user.mention}，計時到囉！")
        asyncio.create_task(task())

    @app_commands.command(name="alarm", description="設定鬧鐘")
    async def alarm(self, interaction: discord.Interaction, country: str, hour: int, minute: int):
        if country not in COUNTRY_TIMEZONES:
            await interaction.response.send_message(f"❌ 不支援的國家: {', '.join(COUNTRY_TIMEZONES.keys())}", ephemeral=True)
            return
        tz = ZoneInfo(COUNTRY_TIMEZONES[country])
        now = datetime.now(tz)
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target_time < now:
            target_time += timedelta(days=1)
        delta_seconds = int((target_time - now).total_seconds())
        delta_formatted = format_duration(delta_seconds)
        await interaction.response.send_message(
            f"⏰ 鬧鐘已設定在 {country} 時間 {target_time.strftime('%H:%M')}，還有 {delta_formatted} 後提醒！",
            ephemeral=True
        )
        async def task():
            await asyncio.sleep(delta_seconds)
            await interaction.channel.send(f"🔔 {interaction.user.mention}，現在是 {country} {target_time.strftime('%H:%M')}，鬧鐘到囉！")
        asyncio.create_task(task())

    @app_commands.command(name="say", description="讓機器人發送訊息")
    async def say(self, interaction: discord.Interaction, message: str, channel_name: str = None, user_id: str = None):
        if not interaction.user.guild_permissions.administrator and interaction.user.id not in SPECIAL_USER_IDS:
            await interaction.response.send_message("❌ 你沒有權限使用此指令", ephemeral=True)
            return
        if user_id:
            try:
                user = await self.bot.fetch_user(int(user_id))
                await user.send(message)
                await interaction.response.send_message(f"✅ 已發送私訊給 {user.name}", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ 發送失敗: {e}", ephemeral=True)
            return
        channel = discord.utils.get(interaction.guild.channels, name=channel_name) if channel_name else interaction.channel
        if not channel:
            await interaction.response.send_message(f"❌ 找不到頻道 `{channel_name}`", ephemeral=True)
            return
        await channel.send(message)
        await interaction.response.send_message(f"✅ 已在 {channel.mention} 發送訊息", ephemeral=True)

# =========================
# 🎮 FunCog
# =========================
class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rps_choices = {"剪刀":"✂️", "石頭":"🪨", "布":"📄"}

    @app_commands.command(name="rps", description="剪刀石頭布")
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
        await interaction.response.send_message(f"你出 {self.rps_choices[choice]} ({choice})\n我出 {self.rps_choices[bot_choice]} ({bot_choice})\n結果：{result}")

    @app_commands.command(name="draw", description="隨機抽籤")
    async def draw(self, interaction: discord.Interaction, options: str):
        items = [o.strip() for o in options.replace(",", " ").split() if o.strip()]
        if len(items) < 2:
            await interaction.response.send_message("❌ 請至少輸入兩個選項", ephemeral=True)
            return
        winner = random.choice(items)
        await interaction.response.send_message(f"🎉 抽籤結果：**{winner}**")
        
        
        
#管理——————
    from discord.ext import commands
from discord import app_commands
import discord

  # 改成你的 Discord ID

class AdminCog(commands.Cog):
    """管理員專用指令"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="kick", description="踢出成員")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "未提供原因"):
        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message("❌ 你沒有權限踢人", ephemeral=True)
            return
        await member.kick(reason=reason)
        await interaction.response.send_message(f"✅ 已踢出 {member.display_name}")

    @app_commands.command(name="ban", description="封禁成員")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "未提供原因"):
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("❌ 你沒有權限封禁成員", ephemeral=True)
            return
        await member.ban(reason=reason)
        await interaction.response.send_message(f"✅ 已封禁 {member.display_name}")

    @app_commands.command(name="restart", description="重啟機器人（僅指定使用者可用）")
    async def restart(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ 你沒有權限重啟機器人", ephemeral=True)
            return
        await interaction.response.send_message("🔄 機器人正在重啟...", ephemeral=True)
        await self.bot.close()

# =========================
# 🔧 Cog 載入函數
# =========================
async def setup_cogs(bot):
    # 先檢查 Cog 是否已存在
    if not bot.get_cog("UtilityCog"):
        await bot.add_cog(UtilityCog(bot))
    if not bot.get_cog("FunCog"):
        await bot.add_cog(FunCog(bot))
    if not bot.get_cog("AdminCog"):
        await bot.add_cog(AdminCog(bot))
        
app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot is running.'


def run_web():
    app.run(host='0.0.0.0', port=PORT)

# ===== Entrypoint =====
if __name__ == '__main__':
    # 開一條 Flask 執行緒，讓 Render 偵測埠口
    threading.Thread(target=run_web, daemon=True).start()


# =========================
# 🚀 啟動 Bot
# =========================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ 已登入：{bot.user} (ID: {bot.user.id})")

async def main():
    await setup_cogs(bot)
    await keep_alive()
    TOKEN = os.getenv("DISCORD_TOKEN")
    

async def main():
    await setup_cogs(bot)   # 載入你的 cogs
    await keep_alive()      # aiohttp 保活
    await bot.start(TOKEN)  # 啟動 Bot

asyncio.run(main())