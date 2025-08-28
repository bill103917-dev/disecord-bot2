from discord.ext import commands
from discord import app_commands
import discord
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# 你原本的輔助函數 (例如 parse_time, format_duration, COUNTRY_TIMEZONES) 請保留
# 這裡我先假設它們已經定義在前面了

SPECIAL_USER_IDS = [1238436456041676853]  # 你要允許使用 /say 的特殊使用者 ID

# =========================
# 📌 UtilityCog (工具指令)
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

    @app_commands.command(name="say", description="讓機器人在頻道或私訊發送訊息")
    @app_commands.describe(channel_name="要發送的頻道名稱（可選，留空則在當前頻道）",
                           user_id="要發送私訊的使用者 ID（可選）",
                           message="要發送的訊息")
    async def say(self, interaction: discord.Interaction, message: str, channel_name: str = None, user_id: str = None):
        # 權限檢查
        if not interaction.user.guild_permissions.administrator and interaction.user.id not in SPECIAL_USER_IDS:
            await interaction.response.send_message("❌ 你沒有權限使用此指令", ephemeral=True)
            return

        # 如果指定 user_id，發送私訊
        if user_id:
            try:
                user = await self.bot.fetch_user(int(user_id))
                await user.send(message)
                await interaction.response.send_message(f"✅ 已發送私訊給 {user.name}", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ 發送失敗: {e}", ephemeral=True)
            return

        # 發送到頻道
        if channel_name:
            channel = discord.utils.get(interaction.guild.channels, name=channel_name)
            if not channel:
                await interaction.response.send_message(f"❌ 找不到頻道 `{channel_name}`", ephemeral=True)
                return
        else:
            channel = interaction.channel

        await channel.send(message)
        await interaction.response.send_message(f"✅ 已在 {channel.mention} 發送訊息", ephemeral=True)

    @app_commands.command(name="help", description="顯示所有指令說明")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📖 指令清單", color=discord.Color.blue())
        embed.add_field(name="/ping", value="測試 Bot 是否在線", inline=False)
        embed.add_field(name="/hello", value="跟你打招呼", inline=False)
        embed.add_field(name="/timer <時間>", value="設定計時器 (例如 10s, 5m, 2h)", inline=False)
        embed.add_field(name="/alarm <國家> <小時> <分鐘>", value="設定鬧鐘", inline=False)
        embed.add_field(name="/say <訊息>", value="讓機器人在頻道或私訊發送訊息 (管理員或特殊使用者限定)", inline=False)
        embed.add_field(name="/rps <選擇>", value="玩剪刀石頭布", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

# =========================
# 🎮 FunCog (娛樂指令)
# =========================
class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    rps_choices = {
        "剪刀": "✂️",
        "石頭": "🪨",
        "布": "📄"
    }

    @app_commands.command(name="rps", description="和機器人玩剪刀石頭布")
    @app_commands.describe(choice="請選擇 剪刀/石頭/布")
    async def rps(self, interaction: discord.Interaction, choice: str):
        import random

        if choice not in self.rps_choices:
            await interaction.response.send_message("❌ 請輸入 剪刀/石頭/布", ephemeral=True)
            return

        bot_choice = random.choice(list(self.rps_choices.keys()))

        # 判斷勝負
        if choice == bot_choice:
            result = "平手 🤝"
        elif (choice == "剪刀" and bot_choice == "布") or \
             (choice == "石頭" and bot_choice == "剪刀") or \
             (choice == "布" and bot_choice == "石頭"):
            result = "你贏了 🎉"
        else:
            result = "你輸了 😢"

        await interaction.response.send_message(
            f"你出 {self.rps_choices[choice]} ({choice})\n"
            f"我出 {self.rps_choices[bot_choice]} ({bot_choice})\n"
            f"結果：{result}"
        )
        
        from discord import app_commands
from discord.ext import commands
import discord
import random

class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="draw", description="隨機抽籤")
    @app_commands.describe(options="輸入多個選項，用逗號或空格分隔")
    async def draw(self, interaction: discord.Interaction, options: str):
        # 將使用者輸入拆分成列表
        if "," in options:
            items = [o.strip() for o in options.split(",") if o.strip()]
        else:
            items = [o.strip() for o in options.split() if o.strip()]

        if not items or len(items) < 2:
            await interaction.response.send_message("❌ 請至少輸入兩個選項", ephemeral=True)
            return

        winner = random.choice(items)
        await interaction.response.send_message(f"🎉 抽籤結果：**{winner}**")
# =========================
# 📌 Cog 載入函數
# =========================
# -----------------------------
# Cog 載入函數
# -----------------------------
# -----------------------------
# Cog 載入函數
# -----------------------------
async def setup_cogs(bot: commands.Bot):
    # 載入工具指令
    await bot.add_cog(UtilityCog(bot))

    # 載入娛樂指令
    await bot.add_cog(FunCog(bot))

    # 載入管理員指令
    await bot.add_cog(AdminCog(bot))

    # 載入抽獎指令
    await bot.add_cog(GiveawayCog(bot))
# =========================
# 🔧 輔助函數
# =========================
def parse_time(timestr: str) -> int:
    """解析像 10s, 5m, 2h 這樣的字串，轉換成秒數"""
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

    if num:  # 沒有單位時，預設秒
        total += int(num)

    if total <= 0:
        raise ValueError("時間必須大於 0 秒")

    return total


def format_duration(seconds: int) -> str:
    """把秒數轉換成 人類可讀格式"""
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

OWNER_ID = 1238436456041676853  # 你的 Discord ID

class AdminCog(commands.Cog):
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
        
#抽獎——————————————————————————
class GiveawayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_giveaways = {}   # message_id: {prize, participants, winners, role, host_id, message}
        self.ended_giveaways = {}

    # -----------------------------
    # 開始抽獎
    # -----------------------------
    @app_commands.command(name="giveaway", description="開始抽獎")
    async def giveaway(self, interaction: discord.Interaction, prize: str, winners: int = 1):
        embed = discord.Embed(title="🎉 抽獎開始！", description=f"獎品：{prize}\n中獎人數：{winners}", color=discord.Color.green())
        msg = await interaction.channel.send(embed=embed)
        self.active_giveaways[msg.id] = {
            "prize": prize,
            "winners": winners,
            "participants": set(),
            "host_id": interaction.user.id,
            "message": msg
        }
        await interaction.response.send_message(f"✅ 抽獎「{prize}」已開始！", ephemeral=True)

    # -----------------------------
    # 參加抽獎
    # -----------------------------
    @app_commands.command(name="join", description="參加抽獎")
    async def join(self, interaction: discord.Interaction):
        if not self.active_giveaways:
            await interaction.response.send_message("❌ 目前沒有抽獎可以參加", ephemeral=True)
            return
        giveaway = list(self.active_giveaways.values())[0]  # 先加入第一個抽獎
        giveaway["participants"].add(interaction.user)
        await interaction.response.send_message("✅ 已加入抽獎！", ephemeral=True)

    # -----------------------------
    # 結束抽獎
    # -----------------------------
    @app_commands.command(name="end_giveaway", description="結束抽獎")
    async def end_giveaway(self, interaction: discord.Interaction, message_id: int):
        data = self.active_giveaways.pop(message_id, None)
        if not data:
            await interaction.response.send_message("❌ 找不到抽獎", ephemeral=True)
            return
        participants = list(data["participants"])
        if not participants:
            await interaction.channel.send(f"❌ 抽獎「{data['prize']}」結束，沒有人參加。")
            return
        winners = random.sample(participants, min(len(participants), data["winners"]))
        mentions = ", ".join(w.mention for w in winners)
        await interaction.channel.send(f"🏆 抽獎「{data['prize']}」結束！恭喜 {mentions} 🎉")
        # 私訊中獎者
        for winner in winners:
            try:
                await winner.send(f"🎉 你在抽獎「{data['prize']}」中獎了！恭喜！")
            except:
                pass
        self.ended_giveaways[message_id] = data
        await interaction.response.send_message("✅ 抽獎已結束", ephemeral=True)

    # -----------------------------
    # 重新抽獎 (reroll)
    # -----------------------------
    @app_commands.command(name="reroll", description="重新抽獎")
    async def reroll(self, interaction: discord.Interaction, message_id: int):
        data = self.ended_giveaways.get(message_id)
        if not data:
            await interaction.response.send_message("❌ 找不到結束的抽獎", ephemeral=True)
            return
        participants = list(data["participants"])
        if not participants:
            await interaction.response.send_message("❌ 沒有人參加，無法重新抽獎", ephemeral=True)
            return
        winners = random.sample(participants, min(len(participants), data["winners"]))
        mentions = ", ".join(w.mention for w in winners)
        await interaction.channel.send(f"🎲 抽獎「{data['prize']}」重新抽獎！恭喜 {mentions} 🎉")
        # 私訊中獎者
        for winner in winners:
            try:
                await winner.send(f"🎉 你在抽獎「{data['prize']}」重新抽獎中中獎了！恭喜！")
            except:
                pass
        await interaction.response.send_message("✅ 已重新抽獎", ephemeral=True)

    # -----------------------------
    # 查看參加者
    # -----------------------------
    @app_commands.command(name="participants", description="查看抽獎參加者")
    async def participants(self, interaction: discord.Interaction, message_id: int):
        data = self.active_giveaways.get(message_id) or self.ended_giveaways.get(message_id)
        if not data:
            await interaction.response.send_message("❌ 找不到抽獎", ephemeral=True)
            return
        if not data["participants"]:
            await interaction.response.send_message("❌ 沒有人參加此抽獎", ephemeral=True)
            return
        participants_list = "\n".join([user.mention for user in data["participants"]])
        embed = discord.Embed(title=f"🎉 抽獎「{data['prize']}」參加者列表",
                              description=participants_list,
                              color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)


# =========================
# 🚀 啟動 Bot
# =========================
intents = discord.Intents.default()
intents.message_content = True  # 如果需要處理文字訊息要開這個

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ 已登入：{bot.user} (ID: {bot.user.id})")

async def main():
    async with bot:
        await setup_cogs(bot)  
        await bot.start("YOUR_BOT_TOKEN")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())