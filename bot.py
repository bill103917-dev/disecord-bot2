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
# HTTP server 保活（Render 專用）
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
    
    # 先定義 Giveaway Cog
class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_giveaways = {}
    # 這裡放所有 giveaway 指令和函式...

# 啟動 Web Server
async def main():
    TOKEN = os.getenv("DISCORD_TOKEN")
    
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True



async def main():
    TOKEN = os.getenv("DISCORD_TOKEN")

    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    bot = commands.Bot(command_prefix="!", intents=intents)
    
    # 啟動 web server
    asyncio.create_task(run_web())

    async with bot:
        # 加載你的 Cog，例如 Giveaway
        await bot.add_cog(Giveaway(bot))
        await bot.start(TOKEN)

asyncio.run(main())

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
# on_ready
# -----------------------------
GUILD_ID = GUILD_IDS = [1244944025748770897, 1227929105018912839]  # 你的伺服器 ID 清單
guild = discord.Object(id=GUILD_ID)

@bot.event
async def on_ready():
    print(f"✅ Bot 已啟動: {bot.user}")
    try:
        synced = await tree.sync(guild=guild)  # 指定伺服器同步
        print(f"📌 已同步 {len(synced)} 個斜線指令到指定伺服器")
    except Exception as e:
        print(f"同步指令失敗: {e}")
    ping_self.start()

# -----------------------------
# 基本指令
# -----------------------------
@tree.command(name="ping", description="測試 Bot 是否在線")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@tree.command(name="hello", description="打招呼")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello {interaction.user.mention}!")

# -----------------------------
# 計時器
# -----------------------------
@tree.command(name="timer", description="設定計時器")
@app_commands.describe(timestr="計時時間，例如 01:30:00 或 25:00")
async def timer(interaction: discord.Interaction, timestr: str):
    try:
        total_seconds = parse_time(timestr)
    except ValueError as e:
        await interaction.response.send_message(f"❌ {e}", ephemeral=True)
        return
    
    # 立即回應使用者
    await interaction.response.send_message(f"⏳ 計時器開始：{timestr}", ephemeral=True)
    
    # 背景任務
    async def timer_task():
        await asyncio.sleep(total_seconds)
        await interaction.channel.send(f"⏰ {interaction.user.mention}，計時到囉！")
    
    asyncio.create_task(timer_task())
# -----------------------------
# 鬧鐘
# -----------------------------
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
    
    # 立即回應使用者
    await interaction.response.send_message(
        f"⏰ 鬧鐘已設定在 {country} 時間 {target_time.strftime('%H:%M')}，還有 {delta_formatted} 後提醒！",
        ephemeral=True
    )
    
    # 背景任務
    async def alarm_task():
        await asyncio.sleep(delta_seconds)
        await interaction.channel.send(
            f"🔔 {interaction.user.mention}，現在是 {country} {target_time.strftime('%H:%M')}，鬧鐘到囉！"
        )
    
    asyncio.create_task(alarm_task())

# -----------------------------
# 公告
# -----------------------------
@tree.command(name="announce", description="發布公告（管理員限定）")
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
# 好玩功能
# -----------------------------
@tree.command(name="add", description="加法運算")
async def add(interaction: discord.Interaction, a: int, b: int):
    await interaction.response.send_message(f"{a} + {b} = {a+b}")

@tree.command(name="sub", description="減法運算")
async def sub(interaction: discord.Interaction, a: int, b: int):
    await interaction.response.send_message(f"{a} - {b} = {a-b}")

@tree.command(name="mul", description="乘法運算")
async def mul(interaction: discord.Interaction, a: int, b: int):
    await interaction.response.send_message(f"{a} × {b} = {a*b}")

@tree.command(name="div", description="除法運算")
async def div(interaction: discord.Interaction, a: int, b: int):
    if b == 0:
        await interaction.response.send_message("❌ 不能除以 0")
    else:
        await interaction.response.send_message(f"{a} ÷ {b} = {a/b}")

@tree.command(name="rps", description="剪刀石頭布")
@app_commands.describe(choice="你的選擇：rock, paper, scissors")
async def rps(interaction: discord.Interaction, choice: str):
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

@tree.command(name="dice", description="擲骰子")
async def dice(interaction: discord.Interaction):
    num = random.randint(1,6)
    await interaction.response.send_message(f"🎲 你擲出了 {num}")

# -----------------------------
# 管理功能
# -----------------------------
@tree.command(name="clear", description="清理訊息")
@app_commands.describe(amount="要刪除的訊息數量")
async def clear(interaction: discord.Interaction, amount: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ 你沒有權限刪除訊息", ephemeral=True)
        return
    deleted = await interaction.channel.purge(limit=amount+1)
    await interaction.response.send_message(f"✅ 已刪除 {len(deleted)-1} 則訊息", ephemeral=True)

@tree.command(name="kick", description="踢出成員")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "未提供原因"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("❌ 你沒有權限踢人", ephemeral=True)
        return
    await member.kick(reason=reason)
    await interaction.response.send_message(f"✅ 已踢出 {member.display_name}")

@tree.command(name="ban", description="封禁成員")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "未提供原因"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ 你沒有權限封禁成員", ephemeral=True)
        return
    await member.ban(reason=reason)
    await interaction.response.send_message(f"✅ 已封禁 {member.display_name}")

# -----------------------------
# 重啟機器人（指定使用者）
# -----------------------------
OWNER_ID = 1238436456041676853  # <-- 改成你的 Discord ID

@tree.command(name="restart", description="重啟機器人（只有指定使用者可執行）")
async def restart(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ 你沒有權限重啟機器人", ephemeral=True)
        return
    await interaction.response.send_message("🔄 機器人正在重啟...", ephemeral=True)
    await bot.close()

# -----------------------------
# Giveaway 系統
# -----------------------------
@tree.command(name="giveaway", description="開始一個抽獎")
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
    year = now.year
    end_time = datetime(year, 月份, 日期, 小時, 分鐘, tzinfo=tz)
    if end_time <= now:
        year += 1
        end_time = datetime(year, 月份, 日期, 小時, 分鐘, tzinfo=tz)
    if 人數 < 1:
        await interaction.response.send_message("❌ 中獎人數至少 1", ephemeral=True)
        return

    # 立即回應使用者
    await interaction.response.send_message(
        f"✅ 抽獎開始！獎品：{獎品}，中獎人數：{人數}，結束時間：{end_time.strftime('%m月%d日 %H:%M')}",
        ephemeral=True
    )

    async def giveaway_task():
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
        active_giveaway = {
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

        ten_seconds_msg = None

        while datetime.now(tz) < end_time and not active_giveaway["ended"]:
            await msg.edit(embed=create_embed())
            delta = end_time - datetime.now(tz)

            if delta.total_seconds() <= 60 and not active_giveaway["one_minute_notified"]:
                await interaction.channel.send(f"⏰ 抽獎「{獎品}」還剩 1 分鐘！快來參加！")
                active_giveaway["one_minute_notified"] = True

            if delta.total_seconds() <= 10 and not active_giveaway["ten_seconds_notified"]:
                for i in range(10, 0, -1):
                    if ten_seconds_msg is None:
                        ten_seconds_msg = await interaction.channel.send(f"⏱️ 抽獎「{獎品}」 {i} 秒後結束！")
                    else:
                        await ten_seconds_msg.edit(content=f"⏱️ 抽獎「{獎品}」 {i} 秒後結束！")
                    await asyncio.sleep(1)
                active_giveaway["ten_seconds_notified"] = True
                if ten_seconds_msg:
                    await ten_seconds_msg.delete()
                break

            await asyncio.sleep(60)

        if not active_giveaway["ended"]:
            participants_list = list(participants)
            if len(participants_list) >= 人數:
                winners = random.sample(participants_list, 人數)
                winners_mentions = ", ".join([w.mention for w in winners])
                embed = discord.Embed(
                    title="🏆 抽獎結束！",
                    description=f"🎉 恭喜 {winners_mentions} 獲得 **{獎品}**！",
                    color=discord.Color.green()
                )
            elif participants_list:
                winners_mentions = ", ".join([w.mention for w in participants_list])
                embed = discord.Embed(
                    title="🏆 抽獎結束！",
                    description=f"🎉 人數不足，所有參加者都中獎！({winners_mentions})\n獎品：**{獎品}**",
                    color=discord.Color.orange()
                )
            else:
                embed = discord.Embed(
                    title="🏆 抽獎結束！",
                    description=f"😢 沒有人參加抽獎。獎品 **{獎品}** 流標。",
                    color=discord.Color.red()
                )
            await msg.edit(embed=embed)

    asyncio.create_task(giveaway_task())


# -----------------------------
# 啟動 Bot
# -----------------------------
bot.add_cog(Giveaway(bot))

TOKEN = os.getenv("DISCORD_TOKEN")