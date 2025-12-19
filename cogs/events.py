import discord
from discord.ext import commands
from datetime import datetime, timedelta
from utils import *

spam_tracker = {}
raid_tracker = {}
antinuke_tracker = {}

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        if message.guild:
            guild_settings = get_guild_settings(message.guild.id)
            
            if guild_settings.get("antispam_enabled"):
                uid = message.author.id
                now = datetime.utcnow()
                
                if uid not in spam_tracker:
                    spam_tracker[uid] = []
                
                spam_tracker[uid].append(now)
                spam_tracker[uid] = [t for t in spam_tracker[uid] if (now - t).seconds < 5]
                
                if len(spam_tracker[uid]) >= 5:
                    try:
                        await message.author.timeout(timedelta(minutes=5), reason="Auto-mod: Spam detected")
                        add_mod_log(message.guild.id, "auto_timeout", message.author.id, self.bot.user.id, "Spam detected")
                        
                        embed = create_embed(f"{EMOJIS['deny']} Auto-timeout: **{message.author}** (Spam detected)", "warning")
                        await message.channel.send(embed=embed)
                        
                        spam_tracker[uid] = []
                    except:
                        pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_settings = get_guild_settings(member.guild.id)
        
        if guild_settings.get("antiraid_enabled"):
            gid = member.guild.id
            now = datetime.utcnow()
            
            if gid not in raid_tracker:
                raid_tracker[gid] = []
            
            raid_tracker[gid].append(now)
            raid_tracker[gid] = [t for t in raid_tracker[gid] if (now - t).seconds < 10]
            
            if len(raid_tracker[gid]) >= 10:
                try:
                    await member.kick(reason="Anti-raid: Potential raid detected")
                    add_mod_log(member.guild.id, "auto_kick", member.id, self.bot.user.id, "Raid detected")
                    
                    log_embed = create_embed(f"{EMOJIS['deny']} Auto-kicked: **{member}** (Raid detected)", "warning")
                    await log_action(member.guild, log_embed)
                except:
                    pass

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild = channel.guild
        guild_settings = get_guild_settings(guild.id)
        
        if guild_settings.get("antinuke_enabled"):
            try:
                async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
                    if entry.user.id == self.bot.user.id or entry.user.id == OWNER_ID:
                        return
                    
                    uid = entry.user.id
                    now = datetime.utcnow()
                    
                    if uid not in antinuke_tracker:
                        antinuke_tracker[uid] = {"channel_deletes": []}
                    if "channel_deletes" not in antinuke_tracker[uid]:
                        antinuke_tracker[uid]["channel_deletes"] = []
                    
                    antinuke_tracker[uid]["channel_deletes"].append(now)
                    antinuke_tracker[uid]["channel_deletes"] = [t for t in antinuke_tracker[uid]["channel_deletes"] if (now - t).seconds < 60]
                    
                    if len(antinuke_tracker[uid]["channel_deletes"]) >= 3:
                        member = guild.get_member(uid)
                        if member:
                            try:
                                await member.ban(reason="Anti-nuke: Mass channel deletion detected")
                                add_mod_log(guild.id, "antinuke_ban", uid, self.bot.user.id, "Mass channel deletion")
                                
                                log_embed = create_embed(f"{EMOJIS['deny']} Anti-nuke: Banned **{member}** (Mass channel deletion)", "error")
                                await log_action(guild, log_embed)
                            except:
                                pass
            except:
                pass

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        guild = role.guild
        guild_settings = get_guild_settings(guild.id)
        
        if guild_settings.get("antinuke_enabled"):
            try:
                async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
                    if entry.user.id == self.bot.user.id or entry.user.id == OWNER_ID:
                        return
                    
                    uid = entry.user.id
                    now = datetime.utcnow()
                    
                    if uid not in antinuke_tracker:
                        antinuke_tracker[uid] = {"role_deletes": []}
                    if "role_deletes" not in antinuke_tracker[uid]:
                        antinuke_tracker[uid]["role_deletes"] = []
                    
                    antinuke_tracker[uid]["role_deletes"].append(now)
                    antinuke_tracker[uid]["role_deletes"] = [t for t in antinuke_tracker[uid]["role_deletes"] if (now - t).seconds < 60]
                    
                    if len(antinuke_tracker[uid]["role_deletes"]) >= 3:
                        member = guild.get_member(uid)
                        if member:
                            try:
                                await member.ban(reason="Anti-nuke: Mass role deletion detected")
                                add_mod_log(guild.id, "antinuke_ban", uid, self.bot.user.id, "Mass role deletion")
                                
                                log_embed = create_embed(f"{EMOJIS['deny']} Anti-nuke: Banned **{member}** (Mass role deletion)", "error")
                                await log_action(guild, log_embed)
                            except:
                                pass
            except:
                pass

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        guild_settings = get_guild_settings(guild.id)
        
        if guild_settings.get("antinuke_enabled"):
            try:
                async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                    if entry.user.id == self.bot.user.id or entry.user.id == OWNER_ID:
                        return
                    
                    uid = entry.user.id
                    now = datetime.utcnow()
                    
                    if uid not in antinuke_tracker:
                        antinuke_tracker[uid] = {"bans": []}
                    if "bans" not in antinuke_tracker[uid]:
                        antinuke_tracker[uid]["bans"] = []
                    
                    antinuke_tracker[uid]["bans"].append(now)
                    antinuke_tracker[uid]["bans"] = [t for t in antinuke_tracker[uid]["bans"] if (now - t).seconds < 60]
                    
                    if len(antinuke_tracker[uid]["bans"]) >= 5:
                        member = guild.get_member(uid)
                        if member:
                            try:
                                roles_to_remove = [r for r in member.roles if r.permissions.ban_members and r < guild.me.top_role]
                                await member.remove_roles(*roles_to_remove, reason="Anti-nuke: Mass ban detected")
                                add_mod_log(guild.id, "antinuke_strip", uid, self.bot.user.id, "Mass ban detected")
                                
                                log_embed = create_embed(f"{EMOJIS['deny']} Anti-nuke: Stripped roles from **{member}** (Mass ban)", "error")
                                await log_action(guild, log_embed)
                            except:
                                pass
            except:
                pass

async def setup(bot):
    await bot.add_cog(Events(bot))