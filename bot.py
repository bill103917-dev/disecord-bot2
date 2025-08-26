import os
import discord
from discord.ext import tasks
from discord import app_commands
from aiohttp import web
import aiohttp
import random
import asyncio

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
    await interaction.channel.send(f"💬 {message}")

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
import os
import discord
from discord import app_commands
import asyncio
import random
import json

GIVEAWAY_FILE = "giveaways.json"

# -----------------------------
# JSON 儲存函式
# -----------------------------
def load_giveaways():
    if os.path.exists(GIVEAWAY_FILE):
        with open(GIVEAWAY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_giveaways(data):
    with open(GIVEAWAY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# -----------------------------
# /giveaway 指令
# -----------------------------
@bot.tree.command(name="giveaway", description="舉辦抽獎")
@app_commands.describe(
    prize="獎品內容",
    winners="中獎人數",
    hours="小時",
    minutes="分鐘",
    seconds="秒"
)
async def giveaway(
    interaction: discord.Interaction,
    prize: str,
    winners: int = 1,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0
):
    duration = hours*3600 + minutes*60 + seconds
    if duration < 5:
        await interaction.response.send_message("❌ 抽獎時間至少要 5 秒", ephemeral=True)
        return
    if winners < 1:
        await interaction.response.send_message("❌ 得獎人數至少要 1 位", ephemeral=True)
        return

    def format_time(sec):
        h, m, s = sec//3600, (sec%3600)//60, sec%60
        return f"{h:02}:{m:02}:{s:02}"

    embed = discord.Embed(
        title="🎉 抽獎活動 🎉",
        description=f"獎品：**{prize}**\n中獎人數：{winners}\n點擊 🎉 參加！\n⏳ 剩餘時間：{format_time(duration)}",
        color=discord.Color.purple()
    )
    embed.set_footer(text=f"舉辦者：{interaction.user.display_name}")

    message = await interaction.channel.send(embed=embed)
    await message.add_reaction("🎉")
    await interaction.response.send_message(f"✅ 抽獎已開始！訊息 ID：`{message.id}`", ephemeral=True)

    # 倒數更新，每 5 秒刷新一次
    for remaining in range(duration, 0, -5):
        embed.description = f"獎品：**{prize}**\n中獎人數：{winners}\n點擊 🎉 參加！\n⏳ 剩餘時間：{format_time(remaining)}"
        await message.edit(embed=embed)
        await asyncio.sleep(5)

    # 抓取參加者
    message = await interaction.channel.fetch_message(message.id)
    users = await message.reactions[0].users().flatten()
    users = [u for u in users if not u.bot]

    if users:
        if len(users) < winners:
            winners = len(users)
        chosen = random.sample(users, winners)
        mentions = ", ".join([u.mention for u in chosen])
        await interaction.channel.send(f"🎊 恭喜 {mentions} 獲得 **{prize}**！")

        # 存 JSON
        giveaways = load_giveaways()
        giveaways[str(message.id)] = {
            "participants": [u.id for u in users],
            "winners": [u.id for u in chosen],
            "prize": prize
        }
        save_giveaways(giveaways)
    else:
        await interaction.channel.send("😢 沒有人參加抽獎。")

# -----------------------------
# /reroll 指令
# -----------------------------
@bot.tree.command(name="reroll", description="重新抽取抽獎得主")
@app_commands.describe(
    message_id="抽獎活動訊息的 ID",
    winners="要重新抽出的人數 (預設 1)"
)
async def reroll(interaction: discord.Interaction, message_id: str, winners: int = 1):
    giveaways = load_giveaways()
    if message_id not in giveaways:
        await interaction.response.send_message("❌ 找不到抽獎資料，無法重抽。", ephemeral=True)
        return

    participants_ids = giveaways[message_id]["participants"]
    participants = [interaction.guild.get_member(uid) for uid in participants_ids if interaction.guild.get_member(uid)]
    if not participants:
        await interaction.response.send_message("😢 沒有人參加抽獎，無法重抽。", ephemeral=True)
        return

    if winners < 1:
        await interaction.response.send_message("❌ 得獎人數至少要 1 位。", ephemeral=True)
        return
    if winners > len(participants):
        winners = len(participants)

    chosen = random.sample(participants, winners)
    mentions = ", ".join([u.mention for u in chosen])

    # 更新 JSON
    giveaways[message_id]["winners"] = [u.id for u in chosen]
    save_giveaways(giveaways)

    await interaction.channel.send(f"🔄 重新抽獎結果：恭喜 {mentions}！")
    await interaction.response.send_message(f"✅ 已重新抽出 {winners} 位新得主！", ephemeral=True)

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

# -----------------------------
# 啟動 Bot
# -----------------------------
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)