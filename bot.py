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
# -----------------------------
# Giveaway 抽獎系統
# -----------------------------
# -----------------------------
# GiveawayCog 完整版
# -----------------------------
class GiveawayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_giveaways = {}   # message_id: {prize, participants, winners, role, end_time, host_id, message}
        self.ended_giveaways = {}    # 結束抽獎存檔方便 reroll

    # -----------------------------
    # 開始抽獎
    # -----------------------------
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

        embed = discord.Embed(
            title="🎉 抽獎活動開始！",
            description=f"獎品：**{獎品}**\n結束時間：{end_time.strftime('%Y-%m-%d %H:%M')}\n中獎人數：{人數}",
            color=discord.Color.green()
        )
        if 限制角色:
            embed.add_field(name="參加限制", value=f"需要身分組：{限制角色.mention}", inline=False)

        msg = await interaction.channel.send(embed=embed)
        await interaction.response.send_message(f"✅ 抽獎「{獎品}」已開始！", ephemeral=True)

        self.active_giveaways[msg.id] = {
            "end_time": end_time,
            "prize": 獎品,
            "winners": 人數,
            "participants": set(),
            "role": 限制角色.id if 限制角色 else None,
            "host_id": interaction.user.id,
            "message": msg
        }

        async def giveaway_task():
            await asyncio.sleep((end_time - datetime.now(tz)).total_seconds())
            await self.end_giveaway_logic(interaction.channel, msg.id)

        asyncio.create_task(giveaway_task())

    # -----------------------------
    # /join 指令
    # -----------------------------
    @app_commands.command(name="join", description="參加或退出抽獎")
    async def join(self, interaction: discord.Interaction):
        if not self.active_giveaways:
            await interaction.response.send_message("❌ 目前沒有進行中的抽獎。", ephemeral=True)
            return

        for giveaway in self.active_giveaways.values():
            # 角色限制
            if giveaway["role"]:
                member = interaction.guild.get_member(interaction.user.id)
                role = interaction.guild.get_role(giveaway["role"])
                if role not in member.roles:
                    continue

            if interaction.user in giveaway["participants"]:
                class ConfirmView(discord.ui.View):
                    def __init__(self):
                        super().__init__(timeout=30)

                    @discord.ui.button(label="是，我要退出", style=discord.ButtonStyle.danger)
                    async def confirm(self, button: discord.ui.Button, i: discord.Interaction):
                        giveaway["participants"].remove(interaction.user)
                        await i.response.edit_message(content="✅ 你已退出抽獎。", view=None)

                    @discord.ui.button(label="否，繼續參加", style=discord.ButtonStyle.secondary)
                    async def cancel(self, button: discord.ui.Button, i: discord.Interaction):
                        await i.response.edit_message(content="👌 你仍然在抽獎名單中。", view=None)

                await interaction.response.send_message(
                    "⚠️ 你已經參加抽獎，要退出嗎？", view=ConfirmView(), ephemeral=True
                )
                return

            giveaway["participants"].add(interaction.user)
            await interaction.response.send_message("✅ 你已成功加入抽獎！", ephemeral=True)
            return

        await interaction.response.send_message("❌ 沒有符合資格的抽獎。", ephemeral=True)

    # -----------------------------
    # 提前結束抽獎
    # -----------------------------
    @app_commands.command(name="end_giveaway", description="提前結束抽獎（管理員或主辦人）")
    async def end_giveaway(self, interaction: discord.Interaction, message_id: str):
        try:
            message_id = int(message_id)
        except:
            await interaction.response.send_message("❌ message_id 必須是數字。", ephemeral=True)
            return

        data = self.active_giveaways.get(message_id)
        if not data:
            await interaction.response.send_message("❌ 找不到該抽獎或已經結束。", ephemeral=True)
            return

        if not (interaction.user.guild_permissions.administrator or interaction.user.id == data["host_id"]):
            await interaction.response.send_message("❌ 只有管理員或抽獎主辦人可以提前結束抽獎", ephemeral=True)
            return

        await self.end_giveaway_logic(interaction.channel, message_id)
        await interaction.response.send_message("✅ 抽獎已提前結束！", ephemeral=True)

    # -----------------------------
    # 重新抽獎
    # -----------------------------
    @app_commands.command(name="reroll", description="重新抽獎（管理員或抽獎主辦人）")
    async def reroll(self, interaction: discord.Interaction, message_id: str):
        try:
            message_id = int(message_id)
        except:
            await interaction.response.send_message("❌ message_id 必須是數字。", ephemeral=True)
            return

        data = self.ended_giveaways.get(message_id)
        if not data:
            await interaction.response.send_message("❌ 找不到該抽獎或尚未結束。", ephemeral=True)
            return

        if not (interaction.user.guild_permissions.administrator or interaction.user.id == data.get("host_id")):
            await interaction.response.send_message("❌ 只有管理員或抽獎主辦人可以重新抽獎", ephemeral=True)
            return

        if not data["participants"]:
            await interaction.response.send_message("❌ 沒有人參加，無法重新抽獎。", ephemeral=True)
            return

        winners = random.sample(list(data["participants"]), min(data["winners"], len(data["participants"])))
        mentions = ", ".join(w.mention for w in winners)
        await interaction.channel.send(f"🎲 抽獎「{data['prize']}」重新抽獎！恭喜 {mentions} 🎉")
        await interaction.response.send_message("✅ 已重新抽獎！", ephemeral=True)

    # -----------------------------
    # 結束抽獎邏輯
    # -----------------------------
    async def end_giveaway_logic(self, channel, message_id):
        data = self.active_giveaways.pop(message_id, None)
        if not data:
            return

        self.ended_giveaways[message_id] = data
        participants_list = list(data["participants"])
        if not participants_list:
            await channel.send(f"❌ 抽獎「{data['prize']}」結束，沒有人參加。")
            return

        winners = random.sample(participants_list, min(data["winners"], len(participants_list)))
        mentions = ", ".join(w.mention for w in winners)
        await channel.send(f"🏆 抽獎「{data['prize']}」結束！恭喜 {mentions} 🎉")

    # -----------------------------
    # reaction 參加
    # -----------------------------
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        data = self.active_giveaways.get(reaction.message.id)
        if not data:
            return
        if str(reaction.emoji) != "🎉":
            return
        if data["role"]:
            member = reaction.message.guild.get_member(user.id)
            role = reaction.message.guild.get_role(data["role"])
            if role not in member.roles:
                return
        data["participants"].add(user)
# -----------------------------
# 查看參加者
# -----------------------------
@app_commands.command(name="participants", description="查看抽獎參加者（管理員或主辦人）")
async def participants(self, interaction: discord.Interaction, message_id: str):
    try:
        message_id = int(message_id)
    except:
        await interaction.response.send_message("❌ message_id 必須是數字。", ephemeral=True)
        return

    data = self.active_giveaways.get(message_id) or self.ended_giveaways.get(message_id)
    if not data:
        await interaction.response.send_message("❌ 找不到該抽獎。", ephemeral=True)
        return

    if not (interaction.user.guild_permissions.administrator or interaction.user.id == data.get("host_id")):
        await interaction.response.send_message("❌ 只有管理員或抽獎主辦人可以查看參加者名單", ephemeral=True)
        return

    if not data["participants"]:
        await interaction.response.send_message("❌ 目前沒有人參加此抽獎。", ephemeral=True)
        return

    participants_list = "\n".join([user.mention for user in data["participants"]])
    embed = discord.Embed(
        title=f"🎉 抽獎「{data['prize']}」參加者列表",
        description=participants_list,
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

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