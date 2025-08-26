import os
import discord
from discord.ext import tasks
from discord import app_commands
from aiohttp import web
import aiohttp
import random

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
    print(f"✅ Bot is ready! Logged in as {bot.user}")

# -----------------------------
# 排行榜
# -----------------------------
leaderboard = {}  # key = user_id, value = 勝場數

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
# 基本 Slash Commands
# -----------------------------
@bot.tree.command(name="ping", description="測試 Bot 是否在線")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@bot.tree.command(name="hello", description="打招呼")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello {interaction.user.mention}!")

@bot.tree.command(name="userinfo", description="查看使用者資訊")
@app_commands.describe(member="要查詢的使用者")
async def userinfo(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    embed = discord.Embed(title=f"{member}'s Info", color=discord.Color.blue())
    embed.add_field(name="ID", value=member.id, inline=False)
    embed.add_field(name="Display Name", value=member.display_name, inline=False)
    embed.add_field(name="Joined at", value=member.joined_at, inline=False)
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="serverinfo", description="查看伺服器資訊")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title=f"{guild.name} Info", color=discord.Color.green())
    embed.add_field(name="ID", value=guild.id, inline=False)
    embed.add_field(name="Owner", value=guild.owner, inline=False)
    embed.add_field(name="Member Count", value=guild.member_count, inline=False)
    embed.add_field(name="Created At", value=guild.created_at, inline=False)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    await interaction.response.send_message(embed=embed)

# -----------------------------
# 管理指令
# -----------------------------
@bot.tree.command(name="kick", description="踢出使用者")
@app_commands.describe(member="要踢出的成員", reason="原因")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("❌ 你沒有踢人的權限", ephemeral=True)
        return
    try:
        await member.kick(reason=reason)
        await interaction.response.send_message(f"✅ 已踢出 {member} 原因: {reason}")
    except Exception as e:
        await interaction.response.send_message(f"❌ 無法踢出 {member}: {e}", ephemeral=True)

@bot.tree.command(name="ban", description="封鎖使用者")
@app_commands.describe(member="要封鎖的成員", reason="原因")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ 你沒有封鎖的權限", ephemeral=True)
        return
    try:
        await member.ban(reason=reason)
        await interaction.response.send_message(f"✅ 已封鎖 {member} 原因: {reason}")
    except Exception as e:
        await interaction.response.send_message(f"❌ 無法封鎖 {member}: {e}", ephemeral=True)

@bot.tree.command(name="say", description="讓 Bot 發訊息")
@app_commands.describe(message="Bot 要說的內容")
async def say(interaction: discord.Interaction, message: str):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ 你沒有權限使用這個指令", ephemeral=True)
        return
    await interaction.response.send_message(f"🗣️ {message}")

# -----------------------------
# 好玩/實用指令
# -----------------------------
@bot.tree.command(name="calc", description="計算數學表達式")
@app_commands.describe(expression="例如：2+3*4")
async def calc(interaction: discord.Interaction, expression: str):
    try:
        allowed = "0123456789+-*/(). "
        if any(c not in allowed for c in expression):
            raise ValueError("只能使用數字和 + - * / ( )")
        result = eval(expression)
        await interaction.response.send_message(f"`{expression}` = {result}")
    except Exception as e:
        await interaction.response.send_message(f"❌ 無法計算: {e}")

@bot.tree.command(name="roll", description="擲骰子")
@app_commands.describe(sides="骰子面數，例如 6")
async def roll(interaction: discord.Interaction, sides: int = 6):
    if sides < 2:
        await interaction.response.send_message("骰子至少要有 2 面")
        return
    result = random.randint(1, sides)
    await interaction.response.send_message(f"🎲 擲出 {result} (1-{sides})")

@bot.tree.command(name="choose", description="隨機選一個選項")
@app_commands.describe(options="用空格分開，例如：蘋果 香蕉 西瓜")
async def choose(interaction: discord.Interaction, options: str):
    choices = options.split()
    if not choices:
        await interaction.response.send_message("請至少輸入一個選項")
        return
    result = random.choice(choices)
    await interaction.response.send_message(f"🎯 選中: {result}")

@bot.tree.command(name="coin", description="擲硬幣")
async def coin(interaction: discord.Interaction):
    result = random.choice(["正面", "反面"])
    add_win(interaction.user.id)
    await interaction.response.send_message(f"🪙 擲出 {result}，你獲得 1 勝！")

@bot.tree.command(name="rps", description="剪刀石頭布遊戲")
@app_commands.describe(choice="你的選擇：剪刀 石頭 布")
async def rps(interaction: discord.Interaction, choice: str):
    choice = choice.lower()
    options = ["剪刀", "石頭", "布"]
    if choice not in [o.lower() for o in options]:
        await interaction.response.send_message("請輸入：剪刀、石頭 或 布")
        return
    bot_choice = random.choice(options)
    if choice == bot_choice.lower():
        result = "平手"
    elif (choice == "剪刀" and bot_choice == "布") or \
         (choice == "布" and bot_choice == "石頭") or \
         (choice == "石頭" and bot_choice == "剪刀"):
        result = "你贏了！🎉"
        add_win(interaction.user.id)
    else:
        result = "我贏了！😎"
    await interaction.response.send_message(f"你出: {choice}\n我出: {bot_choice}\n結果: {result}")

@bot.tree.command(name="randomnum", description="隨機數字生成")
@app_commands.describe(min="最小值", max="最大值")
async def randomnum(interaction: discord.Interaction, min: int, max: int):
    if min > max:
        await interaction.response.send_message("❌ 最小值不能大於最大值")
        return
    number = random.randint(min, max)
    if number == max:
        add_win(interaction.user.id)
    await interaction.response.send_message(f"🎲 隨機數字: {number}，最高值算 1 勝！")

# -----------------------------
# 自我保活任務
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