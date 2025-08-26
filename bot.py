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
    print(f"✅ Bot is ready! Logged in as {bot.user}")

# -----------------------------
# 排行榜
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
@bot.tree.command(name="giveaway", description="舉辦抽獎")
@app_commands.describe(prize="獎品內容", duration="抽獎持續時間（秒）")
async def giveaway(interaction: discord.Interaction, prize: str, duration: int):
    if duration < 5:
        await interaction.response.send_message("❌ 抽獎時間至少要 5 秒", ephemeral=True)
        return

    embed = discord.Embed(title="🎉 抽獎活動 🎉", description=f"獎品：**{prize}**\n點擊 🎉 參加！\n⏳ {duration} 秒後抽出得主", color=discord.Color.purple())
    embed.set_footer(text=f"舉辦者：{interaction.user.display_name}")
    
    message = await interaction.channel.send(embed=embed)
    await message.add_reaction("🎉")
    await interaction.response.send_message("✅ 抽獎已開始！", ephemeral=True)

    # 等待時間
    await asyncio.sleep(duration)

    # 抓取參加者
    message = await interaction.channel.fetch_message(message.id)
    users = await message.reactions[0].users().flatten()
    users = [u for u in users if not u.bot]

    if users:
        winner = random.choice(users)
        await interaction.channel.send(f"🎊 恭喜 {winner.mention} 獲得 **{prize}**！")
    else:
        await interaction.channel.send("😢 沒有人參加抽獎。")

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