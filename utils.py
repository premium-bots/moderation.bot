import discord
from discord.ext import commands
import json
from datetime import datetime

OWNER_ID = 1446389892065267773
BOT_NAME = "Mod Bot"

DATA_FILE = "data/moderation.json"
SETTINGS_FILE = "data/settings.json"
WARNINGS_FILE = "data/warnings.json"
JAIL_FILE = "data/jail.json"
LOGS_FILE = "data/logs.json"
ANTINUKE_FILE = "data/antinuke.json"

# Custom Emojis
EMOJIS = {
    "check": "<:checkmark:1448609505091911693>",
    "deny": "<:deny:1448610156462997607>",
    "crown": "<:Crown:1448610320548626544>"
}

# Clean color scheme
COLORS = {
    "success": 0x3ba55d,  # Green
    "error": 0xed4245,    # Red
    "warning": 0xfaa81a,  # Yellow
    "info": 0x5865f2,     # Blurple
    "neutral": 0x2b2d31   # Dark gray
}

def load_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

def get_guild_settings(guild_id):
    settings = load_json(SETTINGS_FILE)
    gid = str(guild_id)
    if gid not in settings:
        settings[gid] = {
            "log_channel": None,
            "jail_role": None,
            "mute_role": None,
            "mod_roles": [],
            "admin_roles": [],
            "protected_roles": [],
            "automod_enabled": False,
            "antispam_enabled": False,
            "antiraid_enabled": False,
            "antinuke_enabled": False,
            "slowmode_auto": False,
            "dm_on_action": True,
            "max_warnings": 5,
            "vanity_protection": False
        }
        save_json(SETTINGS_FILE, settings)
    return settings[gid]

def get_warnings(guild_id, user_id):
    warnings_data = load_json(WARNINGS_FILE)
    gid = str(guild_id)
    uid = str(user_id)
    if gid not in warnings_data:
        warnings_data[gid] = {}
    if uid not in warnings_data[gid]:
        warnings_data[gid][uid] = []
    return warnings_data[gid][uid]

def add_warning(guild_id, user_id, moderator_id, reason):
    warnings_data = load_json(WARNINGS_FILE)
    gid = str(guild_id)
    uid = str(user_id)
    if gid not in warnings_data:
        warnings_data[gid] = {}
    if uid not in warnings_data[gid]:
        warnings_data[gid][uid] = []
    warnings_data[gid][uid].append({
        "moderator": moderator_id,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat()
    })
    save_json(WARNINGS_FILE, warnings_data)
    return len(warnings_data[gid][uid])

def add_mod_log(guild_id, action, user_id, moderator_id, reason=None, duration=None):
    logs_data = load_json(LOGS_FILE)
    gid = str(guild_id)
    uid = str(user_id)
    mid = str(moderator_id)
    if gid not in logs_data:
        logs_data[gid] = []
    logs_data[gid].append({
        "action": action,
        "user": uid,
        "moderator": mid,
        "reason": reason,
        "duration": duration,
        "timestamp": datetime.utcnow().isoformat()
    })
    if len(logs_data[gid]) > 1000:
        logs_data[gid] = logs_data[gid][-1000:]
    save_json(LOGS_FILE, logs_data)

def get_mod_history(guild_id, user_id):
    logs_data = load_json(LOGS_FILE)
    gid = str(guild_id)
    uid = str(user_id)
    if gid not in logs_data:
        return []
    return [log for log in logs_data[gid] if log.get("user") == uid]

def create_embed(description, color_type="neutral"):
    """Create a clean, minimalist embed"""
    embed = discord.Embed(
        description=description,
        color=COLORS[color_type]
    )
    return embed

def success_embed(message):
    """Quick success embed"""
    return create_embed(f"{EMOJIS['check']} {message}", "success")

def error_embed(message):
    """Quick error embed"""
    return create_embed(f"{EMOJIS['deny']} {message}", "error")

def info_embed(message):
    """Quick info embed"""
    return create_embed(message, "info")

def is_owner():
    async def predicate(ctx):
        return ctx.author.id == OWNER_ID
    return commands.check(predicate)

def is_mod():
    async def predicate(ctx):
        if ctx.author.id == OWNER_ID:
            return True
        if ctx.author.guild_permissions.administrator:
            return True
        guild_settings = get_guild_settings(ctx.guild.id)
        mod_roles = guild_settings.get("mod_roles", [])
        admin_roles = guild_settings.get("admin_roles", [])
        user_role_ids = [role.id for role in ctx.author.roles]
        return any(rid in user_role_ids for rid in mod_roles + admin_roles)
    return commands.check(predicate)

def is_admin():
    async def predicate(ctx):
        if ctx.author.id == OWNER_ID:
            return True
        if ctx.author.guild_permissions.administrator:
            return True
        guild_settings = get_guild_settings(ctx.guild.id)
        admin_roles = guild_settings.get("admin_roles", [])
        user_role_ids = [role.id for role in ctx.author.roles]
        return any(rid in user_role_ids for rid in admin_roles)
    return commands.check(predicate)

async def send_dm(user, embed):
    try:
        await user.send(embed=embed)
        return True
    except:
        return False

async def log_action(guild, embed):
    guild_settings = get_guild_settings(guild.id)
    log_channel_id = guild_settings.get("log_channel")
    if log_channel_id:
        channel = guild.get_channel(log_channel_id)
        if channel:
            try:
                await channel.send(embed=embed)
            except:
                pass