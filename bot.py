# -----------------------------
# imports
# -----------------------------
import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from aiohttp import web
import aiohttp
import pytz

# -----------------------------
# Web 保活
# -----------------------------
async def handle(request):
    return web.Response(text="Bot is alive!")

app = web.Application()
app.add_routes([web.get("/", handle)])
PORT = int(os.environ.get("PORT", 8080))

async def run_web():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"✅ Web server running on port {PORT}")

# -----------------------------
# Bot 初始化
# -----------------------------
TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# -----------------------------
# Ping 自己 Task
# -----------------------------
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

# -----------------------------
# Helper Functions
# -----------------------------
def parse_time(timestr: str) -> int:
    parts = timestr.split(":")
    if len(parts) != 3:
        raise ValueError("時間格式錯誤，請使用 HH:MM:SS")
    h, m, s = map(int, parts)
    return h*3600 + m*60 + s

def format_duration(seconds: int):
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}時{m}分{s}秒"

COUNTRY_TIMEZONES = {
    "Taiwan": "Asia/Taipei",
    "Japan": "Asia/Tokyo",
    "USA": "America/New_York",
    "UK": "Europe/London"
}

# -----------------------------
# FunCog
# -----------------------------
class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="add", description="加法運算")
    async def add(self, interaction: discord.Interaction, a: int, b: int):
        await interaction.response.send_message(f"{a} + {b} = {a+b}")

    @app_commands.command(name="sub", description="減法運算")
    async def sub(self, interaction: discord.Interaction, a: int, b: int):
        await interaction.response.send_message(f"{a} - {b} = {a-b}")

    @app_commands.command(name="mul", description="乘法運算")
    async def mul(self, interaction: discord.Interaction, a: int, b: int):
        await interaction.response.send_message(f"{a} × {b} = {a*b}")

    @app_commands.command(name="div", description="除法運算")
    async def div(self, interaction: discord.Interaction, a: int, b: int):
        if b == 0:
            await interaction.response.send_message("❌ 不能除以 0")
        else:
            await interaction.response.send_message(f"{a} ÷ {b} = {a/b}")

    @app_commands.command(name="rps", description="剪刀石頭布")
    async def rps(self, interaction: discord.Interaction, choice: str):
        options = ["rock", "paper", "scissors"]
        if choice not in options:
            await interaction.response.send_message("❌ 請輸入 rock, paper 或 scissors")
            return
        bot_choice = random.choice(options)
        if choice == bot_choice:
            result = "平手！"
        elif (choice == "rock" and bot_choice == "scissors") or \
             (choice == "scissors" and bot_choice == "paper") or \
             (choice == "paper" and bot_choice == "rock"):
            result = "你贏了！"
        else:
            result = "你輸了！"
        await interaction.response.send_message(f"你選擇：{choice}\nBot 選擇：{bot_choice}\n➡ {result}")

    @app_commands.command(name="dice", description="擲骰子")
    async def dice(self, interaction: discord.Interaction):
        num = random.randint(1,6)
        await interaction.response.send_message(f"🎲 你擲出了 {num}")

# -----------------------------
# UtilityCog
# -----------------------------
class UtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="測試 Bot 是否在線")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message("Pong!")

    @app_commands.command(name="hello", description="打招呼")
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Hello {interaction.user.mention}!")

    @app_commands.command(name="timer", description="設定計時器")
    async def timer(self, interaction: discord.Interaction, timestr: str):
        try:
            total_seconds = parse_time(timestr)
        except ValueError as e:
            await interaction.response.send_message(f"❌ {e}", ephemeral=True)
            return
        await interaction.response.send_message(f"⏳ 計時器開始：{timestr}", ephemeral=True)
        async def timer_task():
            await asyncio.sleep(total_seconds)
            await interaction.channel.send(f"⏰ {interaction.user.mention}，計時到囉！")
        asyncio.create_task(timer_task())

    @app_commands.command(name="alarm", description="設定鬧鐘")
    async def alarm(self, interaction: discord.Interaction, country: str, hour: int, minute: int):
        if country not in COUNTRY_TIMEZONES:
            await interaction.response.send_message(
                f"❌ 不支援的國家，請選擇: {', '.join(COUNTRY_TIMEZONES.keys())}", ephemeral=True
            )
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
        async def alarm_task():
            await asyncio.sleep(delta_seconds)
            await interaction.channel.send(
                f"🔔 {interaction.user.mention}，現在是 {country} {target_time.strftime('%H:%M')}，鬧鐘到囉！"
            )
        asyncio.create_task(alarm_task())

# -----------------------------
# AdminCog
# -----------------------------
OWNER_ID = 1238436456041676853  # 改成你的 Discord ID
class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="announce", description="發布公告（管理員限定）")
    async def announce(self, interaction: discord.Interaction, title: str, content: str, ping_everyone: bool = False):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ 只有管理員能發布公告", ephemeral=True)
            return
        embed = discord.Embed(title=f"📢 {title}", description=content, color=discord.Color.orange())
        embed.set_footer(text=f"發布者：{interaction.user.display_name}")
        mention = "@everyone" if ping_everyone else ""
        await interaction.channel.send(mention, embed=embed)
        await interaction.response.send_message("✅ 公告已發布！", ephemeral=True)

    @app_commands.command(name="clear", description="清理訊息")
    async def clear(self, interaction: discord.Interaction, amount: int):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ 你沒有權限刪除訊息", ephemeral=True)
            return
        deleted = await interaction.channel.purge(limit=amount+1)
        await interaction.response.send_message(f"✅ 已刪除 {len(deleted)-1} 則訊息", ephemeral=True)

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

    @app_commands.command(name="restart", description="重啟機器人（只有指定使用者可執行）")
    async def restart(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ 你沒有權限重啟機器人", ephemeral=True)
            return
        await interaction.response.send_message("🔄 機器人正在重啟...", ephemeral=True)
        await bot.close()

# -----------------------------
# GiveawayCog 完整版
# -----------------------------
class GiveawayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_giveaways = {}

    @app_commands.command(name="giveaway", description="開始一個抽獎")
    @app_commands.describe(
        月份="月份", 日期="日期", 小時="小時", 分鐘="分鐘",
        獎品="獎品", 人數="中獎人數", 限制角色="限定角色"
    )
    async def giveaway(self, interaction: discord.Interaction,
                       月份: int, 日期: int, 小時: int, 分鐘: int,
                       獎品: str, 人數: int = 1, 限制角色: discord.Role = None):
        tz = pytz.timezone("Asia/Taipei")
        now = datetime.now(tz)
        year = now.year
        end_time = datetime(year, 月份, 日期, 小時, 分鐘, tzinfo=tz)
        if end_time <= now:
            year += 1
            end_time = datetime(year, 月份, 日期, 小時, 分鐘, tzinfo=tz)

        await interaction.response.send_message(
            f"✅ 抽獎開始！獎品：{獎品}，中獎人數：{人數}", ephemeral=True
        )

        embed = discord.Embed(
            title="🎉 抽獎活動 🎉",
            description=(
                f"獎品：**{獎品}**\n"
                f"結束時間：{end_time.strftime('%m月%d日 %H:%M')}\n"
                f"中獎人數：{人數}\n"
                + (f"限定身分組：{限制角色.mention}\n" if 限制角色 else "") +
                "輸入 `/join` 或點擊 🎉 參加抽獎"
            ),
            color=discord.Color.gold()
        )

        msg = await interaction.channel.send(embed=embed)
        await msg.add_reaction("🎉")

        participants = set()
        self.active_giveaways[msg.id] = {
            "prize": 獎品,
            "participants": participants,
            "message": msg,
            "end_time": end_time,
            "winners_count": 人數,
            "role": 限制角色.id if 限制角色 else None
        }

        async def giveaway_task():
            while datetime.now(tz) < end_time:
                await asyncio.sleep(60)
            # 結束抽獎
            active = self.active_giveaways.pop(msg.id, None)
            if not active:
                return
            participants_list = list(active["participants"])
            winners_count = active["winners_count"]
            if len(participants_list) >= winners_count:
                winners = random.sample(participants_list, winners_count)
                winners_mentions = ", ".join([w.mention for w in winners])
                embed = discord.Embed(
                    title="🏆 抽獎結束！",
                    description=f"🎉 恭喜 {winners_mentions} 獲得 **{active['prize']}**！",
                    color=discord.Color.green()
                )
            elif participants_list:
                winners_mentions = ", ".join([w.mention for w in participants_list])
                embed = discord.Embed(
                    title="🏆 抽獎結束！",
                    description=f"🎉 人數不足，所有參加者都中獎！({winners_mentions})\n獎品：**{active['prize']}**",
                    color=discord.Color.orange()
                )
            else:
                embed = discord.Embed(
                    title="🏆 抽獎結束！",
                    description=f"😢 沒有人參加抽獎，獎品 **{active['prize']}** 流標。",
                    color=discord.Color.red()
                )
            await msg.edit(embed=embed)

        asyncio.create_task(giveaway_task())

    # 用 reaction 加入抽獎
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        active = self.active_giveaways.get(reaction.message.id)
        if not active:
            return
        if str(reaction.emoji) != "🎉":
            return
        # 檢查角色限制
        if active["role"]:
            member = reaction.message.guild.get_member(user.id)
            role = reaction.message.guild.get_role(active["role"])
            if role not in member.roles:
                return
        active["participants"].add(user)
# -----------------------------
# /join 指令
# -----------------------------
@tree.command(name="join", description="參加目前的抽獎")
async def join(interaction: discord.Interaction):
    joined = False
    for giveaway in bot.get_cog("GiveawayCog").active_giveaways.values():
        # 檢查是否有角色限制
        if giveaway["role"]:
            member = interaction.guild.get_member(interaction.user.id)
            role = interaction.guild.get_role(giveaway["role"])
            if role not in member.roles:
                continue
        giveaway["participants"].add(interaction.user)
        joined = True
    if joined:
        await interaction.response.send_message("✅ 你已成功加入抽獎！", ephemeral=True)
    else:
        await interaction.response.send_message("❌ 目前沒有可加入的抽獎，或你沒有符合參加資格。", ephemeral=True)

# -----------------------------
# on_ready
# -----------------------------
@bot.event
async def on_ready():
    print(f"✅ Bot 已啟動: {bot.user}")
    ping_self.start()
    try:
        synced = await tree.sync()
        print(f"📌 已同步 {len(synced)} 個斜線指令")
    except Exception as e:
        print("同步指令失敗:", e)

# -----------------------------
# 429 自動重試登入
# -----------------------------
async def start_bot_with_retry():
    retry_delay = 10
    max_retries = 5
    attempt = 0
    while attempt < max_retries:
        try:
            async with bot:
                asyncio.create_task(run_web())
                await bot.start(TOKEN)
        except discord.HTTPException as e:
            if e.status == 429:
                attempt += 1
                print(f"⚠️ 遇到 429 Too Many Requests，等待 {retry_delay} 秒後重試 ({attempt}/{max_retries})")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise
        else:
            break
    else:
        print("❌ 已達最大重試次數，無法登入 Discord Bot。")

# -----------------------------
# Cog 加載
# -----------------------------
bot.add_cog(FunCog(bot))
bot.add_cog(UtilityCog(bot))
bot.add_cog(AdminCog(bot))
bot.add_cog(GiveawayCog(bot))

# -----------------------------
# 啟動
# -----------------------------
if __name__ == "__main__":
    asyncio.run(start_bot_with_retry())