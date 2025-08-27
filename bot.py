import os
import discord
from discord.ext import commands
from discord.ext import tasks
from discord import app_commands
from aiohttp import web
import aiohttp
import random
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import os
from datetime import datetime, timedelta


from aiohttp import web

async def handle(request):
    return web.Response(text="Bot is running")

app = web.Application()
app.router.add_get("/", handle)

from aiohttp import web
import os
import asyncio

async def handle(request):
    return web.Response(text="Bot is running")

bot = commands.Bot(...)

app = web.Application()
app.router.add_get("/", handle)

async def run_web():
    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

asyncio.get_event_loop().create_task(run_web())

import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# main.py
bot.load_extension("cogs.giveaway")  # 假設抽獎程式在 cogs/giveaway.py

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user} and commands synced!")

# -----------------------------
# Intents 設定
# -----------------------------
intents = discord.Intents.default()
intents.message_content = True   # 如果你要讓 bot 能讀取訊息內容


bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree   # ✅ 這行很重要！

@bot.event
async def on_ready():
    print(f"✅ Bot 已啟動: {bot.user}")
    synced = await tree.sync()
    print(f"📌 已同步 {len(synced)} 個指令")
    
# -----------------------------
# Discord Bot
# -----------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await start_web()
        guild_id = int(os.getenv("GUILD_ID", 0))
        if guild_id:
            guild = discord.Object(id=guild_id)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()
        ping_self.start()

bot = MyBot()

@bot.event
async def on_ready():
    print(f"✅ Bot 已啟動！登入身分：{bot.user}")
    
    TOKEN = os.getenv("DISCORD_TOKEN")
    
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
    
#計時器   
import discord
from discord.ext import commands
from discord import app_commands
import asyncio


def parse_time(timestr: str) -> int:
    """將 'HH:MM:SS' 或 'MM:SS' 轉成總秒數"""
    parts = timestr.split(":")
    parts = [int(p) for p in parts]
    if len(parts) == 3:  # HH:MM:SS
        hours, minutes, seconds = parts
    elif len(parts) == 2:  # MM:SS
        hours = 0
        minutes, seconds = parts
    else:
        raise ValueError("格式錯誤，請輸入 HH:MM:SS 或 MM:SS")
    return hours * 3600 + minutes * 60 + seconds

@bot.tree.command(name="timer", description="設定計時器（到時間後可選擇是否繼續）")
@app_commands.describe(timestr="計時時間，例如 01:30:00 或 25:00")
async def timer(interaction: discord.Interaction, timestr: str):
    try:
        total_seconds = parse_time(timestr)
    except ValueError as e:
        await interaction.response.send_message(f"❌ {e}", ephemeral=True)
        return

    await interaction.response.send_message(f"⏳ 計時器開始：{timestr}")

    await asyncio.sleep(total_seconds)

    await interaction.channel.send(
        f"⏰ {interaction.user.mention}，計時到囉！你要繼續下一個計時器嗎？ (回覆並請輸入 yes 或 no)"
    )

    def check(m):
        return (
            m.author == interaction.user and
            m.channel == interaction.channel and
            m.content.lower() in ["yes", "no"]
        )

    try:
        msg = await bot.wait_for("message", check=check, timeout=60)
        if msg.content.lower() == "yes":
            await interaction.channel.send("✅ 請輸入新的時間（HH:MM:SS 或 MM:SS）")
            msg2 = await bot.wait_for(
                "message",
                check=lambda m: m.author == interaction.user and m.channel == interaction.channel,
                timeout=60
            )
            await timer(interaction, msg2.content)  # 遞迴呼叫新的計時器
        else:
            await interaction.channel.send("⏹ 計時器結束")
    except asyncio.TimeoutError:
        await interaction.channel.send("⌛ 時間到，但你沒有回覆，計時器結束")

@bot.event
async def on_ready():
    print(f"✅ Bot 已啟動: {bot.user}")
    await tree.sync()

    #重啟機器人
    TOKEN = os.getenv("DISCORD_TOKEN")
    
import discord
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# 你的 Discord ID，只有你可以執行重啟
OWNER_ID = 1238436456041676853  # <-- 換成你的數字ID

@tree.command(
    name="restart",
    description="重啟機器人（只有指定使用者可執行）"
)
async def restart(interaction: discord.Interaction):
    # 檢查使用者是否為擁有者
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ 你沒有權限重啟機器人", ephemeral=True)
        return

    await interaction.response.send_message("🔄 機器人正在重啟...", ephemeral=True)
    await bot.close()  # 關閉 Bot，部署平台會自動重啟

@bot.event
async def on_ready():
    print(f"✅ Bot 已啟動: {bot.user}")
    # 同步全域指令
    synced = await tree.sync()
    print(f"📌 已同步 {len(synced)} 個全域指令")

    
  #鬧鐘——————————————————————————  
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import asyncio

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# 國家對應主要時區
COUNTRY_TIMEZONES = {
    "台灣": "Asia/Taipei",
    "日本": "Asia/Tokyo",
    "韓國": "Asia/Seoul",
    "香港": "Asia/Hong_Kong",
    "英國": "Europe/London",
    "法國": "Europe/Paris",
    "美國東岸": "America/New_York",
    "美國西岸": "America/Los_Angeles",
    "澳洲": "Australia/Sydney"
}

def format_duration(seconds: int) -> str:
    """將秒數轉成 HH:MM:SS"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:02}"

@tree.command(name="alarm", description="設定鬧鐘")
@app_commands.describe(country="國家名稱", hour="小時 (24H)", minute="分鐘")
async def alarm(interaction: discord.Interaction, country: str, hour: int, minute: int):
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
        f"⏰ 鬧鐘已設定在 {country} 時間 {target_time.strftime('%H:%M')}，還有 {delta_formatted} (時:分:秒) 後提醒！"
    )

    await asyncio.sleep(delta_seconds)
    await interaction.channel.send(
        f"🔔 {interaction.user.mention}，現在是 {country} {target_time.strftime('%H:%M')}，鬧鐘到囉！"
    )

@bot.event
async def on_ready():
    print(f"✅ Bot 已啟動: {bot.user}")
    await tree.sync()


# -----------------------------
# 排行榜系統
# -----------------------------
leaderboard = {}

def add_win(user_id, amount=1):
    if user_id in leaderboard:
        leaderboard[user_id] += amount
    else:
        leaderboard[user_id] = amount

@bot.tree.command(name="leaderboard", description="查看排行榜")
async def show_leaderboard(interaction: discord.Interaction):
    if not leaderboard:
        await interaction.response.send_message("目前排行榜沒有資料")
        return
    sorted_board = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    embed = discord.Embed(title="🏆 排行榜", color=discord.Color.gold())
    for i, (user_id, score) in enumerate(sorted_board[:10], start=1):
        user = interaction.guild.get_member(user_id)
        name = user.display_name if user else f"未知使用者({user_id})"
        embed.add_field(name=f"{i}. {name}", value=f"{score} 勝", inline=False)
    await interaction.response.send_message(embed=embed)

# -----------------------------
# 基本指令
# -----------------------------
@bot.tree.command(name="ping", description="測試 Bot 是否在線")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@bot.tree.command(name="hello", description="打招呼")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello {interaction.user.mention}!")

@bot.tree.command(name="say", description="匿名發言")
@app_commands.describe(message="Bot 要說的內容")
async def say(interaction: discord.Interaction, message: str):
    await interaction.response.send_message("✅ 訊息已匿名發送！", ephemeral=True)
    await interaction.channel.send(f" {message}")

# -----------------------------
# 好玩功能
# -----------------------------
@bot.tree.command(name="add", description="加法運算")
async def add(interaction: discord.Interaction, a: int, b: int):
    await interaction.response.send_message(f"{a} + {b} = {a+b}")

@bot.tree.command(name="sub", description="減法運算")
async def sub(interaction: discord.Interaction, a: int, b: int):
    await interaction.response.send_message(f"{a} - {b} = {a-b}")

@bot.tree.command(name="mul", description="乘法運算")
async def mul(interaction: discord.Interaction, a: int, b: int):
    await interaction.response.send_message(f"{a} × {b} = {a*b}")

@bot.tree.command(name="div", description="除法運算")
async def div(interaction: discord.Interaction, a: int, b: int):
    if b == 0:
        await interaction.response.send_message("❌ 不能除以 0")
    else:
        await interaction.response.send_message(f"{a} ÷ {b} = {a/b}")

@bot.tree.command(name="rps", description="剪刀石頭布")
@app_commands.describe(choice="你的選擇：rock, paper, scissors")
async def rps(interaction: discord.Interaction, choice: str):
    options = ["rock", "paper", "scissors"]
    if choice not in options:
        await interaction.response.send_message("❌ 請輸入 rock, paper 或 scissors")
        return
    bot_choice = random.choice(options)
    result = ""
    if choice == bot_choice:
        result = "平手！"
    elif (choice == "rock" and bot_choice == "scissors") or \
         (choice == "scissors" and bot_choice == "paper") or \
         (choice == "paper" and bot_choice == "rock"):
        result = "你贏了！"
        add_win(interaction.user.id)
    else:
        result = "你輸了！"
    await interaction.response.send_message(f"你選擇：{choice}\nBot 選擇：{bot_choice}\n➡ {result}")

@bot.tree.command(name="dice", description="擲骰子")
async def dice(interaction: discord.Interaction):
    num = random.randint(1, 6)
    await interaction.response.send_message(f"🎲 你擲出了 {num}")

# -----------------------------
# 管理功能
# -----------------------------
@bot.tree.command(name="clear", description="清理訊息")
@app_commands.describe(amount="要刪除的訊息數量")
async def clear(interaction: discord.Interaction, amount: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ 你沒有權限刪除訊息", ephemeral=True)
        return
    deleted = await interaction.channel.purge(limit=amount+1)
    await interaction.response.send_message(f"✅ 已刪除 {len(deleted)-1} 則訊息", ephemeral=True)

@bot.tree.command(name="kick", description="踢出成員")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "未提供原因"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("❌ 你沒有權限踢人", ephemeral=True)
        return
    await member.kick(reason=reason)
    await interaction.response.send_message(f"✅ 已踢出 {member.display_name}")

@bot.tree.command(name="ban", description="封禁成員")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "未提供原因"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ 你沒有權限封禁成員", ephemeral=True)
        return
    await member.ban(reason=reason)
    await interaction.response.send_message(f"✅ 已封禁 {member.display_name}")

# -----------------------------
# 公告系統
# -----------------------------
@bot.tree.command(name="announce", description="發布公告（管理員限定）")
@app_commands.describe(title="公告標題", content="公告內容", ping_everyone="是否要 @everyone")
async def announce(interaction: discord.Interaction, title: str, content: str, ping_everyone: bool = False):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ 只有管理員能發布公告", ephemeral=True)
        return
    
    embed = discord.Embed(title=f"📢 {title}", description=content, color=discord.Color.orange())
    embed.set_footer(text=f"發布者：{interaction.user.display_name}")
    
    mention = "@everyone" if ping_everyone else ""
    await interaction.channel.send(mention, embed=embed)
    await interaction.response.send_message("✅ 公告已發布！", ephemeral=True)

# -----------------------------
# 抽獎系統
# -----------------------------
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
from datetime import datetime
import pytz

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_giveaways = {}

    @app_commands.command(name="giveaway", description="開始一個抽獎")
    @app_commands.describe(
        月份="請輸入月份 (1-12)",
        日期="請輸入日期 (1-31)",
        小時="請輸入小時 (0-23)",
        分鐘="請輸入分鐘 (0-59)",
        獎品="要抽出的獎品",
        人數="中獎人數，預設為 1",
        限制角色="限定參加的身分組 (可選)"
    )
    async def giveaway(
        self,
        interaction: discord.Interaction,
        月份: int,
        日期: int,
        小時: int,
        分鐘: int,
        獎品: str,
        人數: int = 1,
        限制角色: discord.Role = None
    ):
        tz = pytz.timezone("Asia/Taipei")
        now = datetime.now(tz)

        # 補上今年，若已過則往下一年
        year = now.year
        end_time = datetime(year, 月份, 日期, 小時, 分鐘, tzinfo=tz)
        if end_time <= now:
            year += 1
            end_time = datetime(year, 月份, 日期, 小時, 分鐘, tzinfo=tz)

        if 人數 < 1:
            await interaction.response.send_message("❌ 中獎人數必須至少 1！", ephemeral=True)
            return

        def create_embed():
            delta = end_time - datetime.now(tz)
            total_minutes = max(int(delta.total_seconds() // 60), 0)
            hours, minutes = divmod(total_minutes, 60)
            desc = (
                f"獎品：**{獎品}**\n"
                f"結束時間：{end_time.strftime('%m月%d日 %H:%M')}\n"
                f"中獎人數：{人數}\n"
                + (f"限定身分組：{限制角色.mention}\n" if 限制角色 else "") +
                f"剩餘時間：{hours}時{minutes}分（每分鐘更新）\n"
                "👉 輸入 `/join` 或點擊 🎉 來參加！"
            )
            return discord.Embed(title="🎉 抽獎活動 🎉", description=desc, color=discord.Color.gold())

        msg = await interaction.channel.send(embed=create_embed())
        await msg.add_reaction("🎉")

        participants = set()
        self.active_giveaways[msg.id] = {
            "prize": 獎品,
            "participants": participants,
            "message": msg,
            "end_time": end_time,
            "ended": False,
            "host": interaction.user.id,
            "winners": 人數,
            "role": 限制角色.id if 限制角色 else None,
            "one_minute_notified": False,
            "ten_seconds_notified": False
        }

        await interaction.response.send_message(
            f"✅ 抽獎開始！獎品：{獎品}，中獎人數：{人數}，結束時間：{end_time.strftime('%m月%d日 %H:%M')}",
            ephemeral=True
        )

        ten_seconds_msg = None  # 用來更新最後 10 秒倒數

        # 每分鐘更新剩餘時間
        while datetime.now(tz) < end_time and not self.active_giveaways[msg.id]["ended"]:
            await msg.edit(embed=create_embed())
            delta = end_time - datetime.now(tz)

            # 剩餘 1 分鐘提醒
            if delta.total_seconds() <= 60 and not self.active_giveaways[msg.id]["one_minute_notified"]:
                await interaction.channel.send(f"⏰ 抽獎「{獎品}」還剩 1 分鐘！快來參加！")
                self.active_giveaways[msg.id]["one_minute_notified"] = True

            # 剩餘 10 秒倒數
            if delta.total_seconds() <= 10 and not self.active_giveaways[msg.id]["ten_seconds_notified"]:
                for i in range(10, 0, -1):
                    if ten_seconds_msg is None:
                        ten_seconds_msg = await interaction.channel.send(f"⏱️ 抽獎「{獎品}」 {i} 秒後結束！")
                    else:
                        await ten_seconds_msg.edit(content=f"⏱️ 抽獎「{獎品}」 {i} 秒後結束！")
                    await asyncio.sleep(1)
                self.active_giveaways[msg.id]["ten_seconds_notified"] = True
                # 抽獎結束前刪除倒數訊息
                if ten_seconds_msg:
                    await ten_seconds_msg.delete()
                break

            await asyncio.sleep(60)

        if not self.active_giveaways[msg.id]["ended"]:
            await self.end_giveaway(msg.id)

    @app_commands.command(name="join", description="參加抽獎")
    async def join(self, interaction: discord.Interaction):
        for giveaway_id, data in self.active_giveaways.items():
            if not data["ended"]:
                if data["role"] and data["role"] not in [r.id for r in interaction.user.roles]:
                    await interaction.response.send_message("❌ 你沒有參加這個抽獎的資格！", ephemeral=True)
                    return
                data["participants"].add(interaction.user)
                await interaction.response.send_message("🎉 你已經參加抽獎！", ephemeral=True)
                return
        await interaction.response.send_message("❌ 目前沒有正在進行的抽獎。", ephemeral=True)

    async def end_giveaway(self, msg_id):
        data = self.active_giveaways[msg_id]
        data["ended"] = True
        prize = data["prize"]
        participants = list(data["participants"])
        winners_num = data["winners"]

        if len(participants) >= winners_num:
            winners = random.sample(participants, winners_num)
            winners_mentions = ", ".join([w.mention for w in winners])
            embed = discord.Embed(
                title="🏆 抽獎結束！",
                description=f"🎉 恭喜 {winners_mentions} 獲得 **{prize}**！",
                color=discord.Color.green()
            )
        elif participants:
            winners_mentions = ", ".join([w.mention for w in participants])
            embed = discord.Embed(
                title="🏆 抽獎結束！",
                description=f"🎉 人數不足，所有參加者都中獎！({winners_mentions})\n獎品：**{prize}**",
                color=discord.Color.orange()
            )
        else:
            embed = discord.Embed(
                title="🏆 抽獎結束！",
                description=f"😢 沒有人參加抽獎。獎品 **{prize}** 流標。",
                color=discord.Color.red()
            )

        await data["message"].edit(embed=embed)

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
    
# -----------------------------
# 自我保活
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
                
@bot.event
async def on_ready():
    print(f"✅ Bot 已啟動！登入身分：{bot.user}")
    try:
        synced = await tree.sync()
        print(f"📌 已同步 {len(synced)} 個斜線指令")
    except Exception as e:
        print(f"同步指令失敗: {e}")

# -----------------------------
# 啟動 Bot
# -----------------------------

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)