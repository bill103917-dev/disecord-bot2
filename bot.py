import os
import discord
from discord.ext import tasks
from discord import app_commands
from aiohttp import web
import aiohttp
import random
import asyncio
import json

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
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.send(mention, embed=embed)

# -----------------------------
# 抽獎系統
# -----------------------------
GIVEAWAY_FILE = "giveaways.json"

def load_giveaways():
    if os.path.exists(GIVEAWAY_FILE):
        with