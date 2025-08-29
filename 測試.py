import os
import asyncio
from discord.ext import commands
import discord

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ 已登入：{bot.user} (ID: {bot.user.id})")

async def main():
    # 先啟動保活服務
    await keep_alive()

    # 載入所有 Cog
    await setup_cogs(bot)

    # 同步指令，只執行一次
    try:
        await bot.tree.sync()
        print("✅ 指令同步完成")
    except Exception as e:
        print(f"⚠️ 指令同步失敗: {e}")

    # 啟動 Bot
    await bot.start(TOKEN)

if __name__ == "__main__":
    # 使用 asyncio.run 啟動主程序
    asyncio.run(main())