import discord
from discord.ext import commands
import os
import json

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="em-", intents=intents, help_command=None)

OWNER_ID = 1446389892065267773
BOT_NAME = "Mod Bot"

# Data directory setup
os.makedirs("data", exist_ok=True)

# Initialize JSON files if they don't exist
def init_json_files():
    files = {
        "data/moderation.json": {},
        "data/settings.json": {},
        "data/warnings.json": {},
        "data/jail.json": {},
        "data/logs.json": {},
        "data/antinuke.json": {}
    }
    
    for file, default_data in files.items():
        if not os.path.exists(file):
            with open(file, "w") as f:
                json.dump(default_data, f, indent=2)

init_json_files()

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online!")
    print(f"🔨 Moderation Bot Ready")
    print(f"🌍 Connected to {len(bot.guilds)} servers")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name="over the server | em-help"
        )
    )

async def load_cogs():
    cogs = [
        "cogs.moderation",
        "cogs.channel_management",
        "cogs.role_management",
        "cogs.advanced_moderation",
        "cogs.settings",
        "cogs.protection",
        "cogs.help_system",
        "cogs.events"
    ]
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded {cog}")
        except Exception as e:
            print(f"❌ Failed to load {cog}: {e}")

@bot.event
async def on_command_error(ctx, error):
    EMOJIS = {
        "deny": "<:deny:1448610156462997607>"
    }
    
    def error_embed(msg):
        return discord.Embed(description=f"{EMOJIS['deny']} {msg}", color=0xed4245)
    
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=error_embed(f"Missing argument: `{error.param.name}`"))
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send(embed=error_embed("Member not found."))
    elif isinstance(error, commands.RoleNotFound):
        await ctx.send(embed=error_embed("Role not found."))
    elif isinstance(error, commands.ChannelNotFound):
        await ctx.send(embed=error_embed("Channel not found."))
    elif isinstance(error, commands.CheckFailure):
        await ctx.send(embed=error_embed("You don't have permission to use this command."))
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        print(f"Error: {error}")

async def main():
    async with bot:
        await load_cogs()
        token = ('MTQ1MDY1MTQ5NzI5NjgyNjQ1MQ.GDu-3U.9dAHTH3ZUiGHVxDGEXkRwQ0CfMoqXapHGjyAXg')
        if token:
            await bot.start(token)
        else:
            print("❌ DISCORD_TOKEN not found in environment variables!")
            print("Please set your Discord bot token as a secret named 'DISCORD_TOKEN'")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())