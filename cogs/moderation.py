import discord
from discord.ext import commands
from datetime import datetime, timedelta
from utils import *

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @is_mod()
    async def kick(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role and ctx.author.id != OWNER_ID:
            return await ctx.send(embed=e("❌ Error", f"{ctx.author.mention}, you cannot kick someone with a higher or equal role!", COLORS["error"], self.bot.user))
        
        guild_settings = get_guild_settings(ctx.guild.id)
        
        if guild_settings.get("dm_on_action"):
            dm_embed = e("👢 Kicked", f"You have been kicked from **{ctx.guild.name}**\n\n**Reason:** {reason}\n**Moderator:** {ctx.author.mention}", bot_user=self.bot.user)
            await send_dm(member, dm_embed)
        
        await member.kick(reason=f"{reason} | By: {ctx.author}")
        add_mod_log(ctx.guild.id, "kick", member.id, ctx.author.id, reason)
        
        embed = e("👢 Member Kicked", f"**User:** {member.mention}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}", COLORS["success"], self.bot.user)
        await ctx.send(embed=embed)
        
        log_embed = e("👢 Member Kicked", f"**User:** {member} ({member.id})\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}", bot_user=self.bot.user)
        await log_action(ctx.guild, log_embed)

    @commands.command()
    @is_mod()
    async def ban(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role and ctx.author.id != OWNER_ID:
            return await ctx.send(embed=e("❌ Error", f"{ctx.author.mention}, you cannot ban someone with a higher or equal role!", COLORS["error"], self.bot.user))
        
        guild_settings = get_guild_settings(ctx.guild.id)
        
        if guild_settings.get("dm_on_action"):
            dm_embed = e("🔨 Banned", f"You have been banned from **{ctx.guild.name}**\n\n**Reason:** {reason}\n**Moderator:** {ctx.author.mention}", bot_user=self.bot.user)
            await send_dm(member, dm_embed)
        
        await member.ban(reason=f"{reason} | By: {ctx.author}", delete_message_days=1)
        add_mod_log(ctx.guild.id, "ban", member.id, ctx.author.id, reason)
        
        embed = e("🔨 Member Banned", f"**User:** {member.mention}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}", COLORS["success"], self.bot.user)
        await ctx.send(embed=embed)
        
        log_embed = e("🔨 Member Banned", f"**User:** {member} ({member.id})\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}", bot_user=self.bot.user)
        await log_action(ctx.guild, log_embed)

    @commands.command()
    @is_mod()
    async def softban(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role and ctx.author.id != OWNER_ID:
            return await ctx.send(embed=e("❌ Error", f"{ctx.author.mention}, you cannot softban someone with a higher or equal role!", COLORS["error"], self.bot.user))
        
        await member.ban(reason=f"Softban: {reason} | By: {ctx.author}", delete_message_days=7)
        await ctx.guild.unban(member, reason="Softban complete")
        add_mod_log(ctx.guild.id, "softban", member.id, ctx.author.id, reason)
        
        embed = e("🔨 Member Softbanned", f"**User:** {member.mention}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}\n\n*User's messages have been deleted*", COLORS["success"], self.bot.user)
        await ctx.send(embed=embed)

    @commands.command()
    @is_owner()
    async def hardban(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        mod_data = load_json(DATA_FILE)
        gid = str(ctx.guild.id)
        if gid not in mod_data:
            mod_data[gid] = {"hardbans": []}
        if "hardbans" not in mod_data[gid]:
            mod_data[gid]["hardbans"] = []
        
        mod_data[gid]["hardbans"].append({
            "user_id": member.id,
            "username": str(member),
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "moderator": ctx.author.id
        })
        save_json(DATA_FILE, mod_data)
        
        guild_settings = get_guild_settings(ctx.guild.id)
        if guild_settings.get("dm_on_action"):
            dm_embed = e("⛔ Permanently Banned", f"You have been permanently banned from **{ctx.guild.name}**\n\n**Reason:** {reason}\n\nThis ban cannot be appealed.", bot_user=self.bot.user)
            await send_dm(member, dm_embed)
        
        await member.ban(reason=f"HARDBAN: {reason} | By: {ctx.author}", delete_message_days=7)
        add_mod_log(ctx.guild.id, "hardban", member.id, ctx.author.id, reason)
        
        embed = e("⛔ Member Permanently Banned", f"**User:** {member.mention}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}\n\n*This user cannot be unbanned normally*", COLORS["error"], self.bot.user)
        await ctx.send(embed=embed)

    @commands.command()
    @is_mod()
    async def unban(self, ctx, user_id: int, *, reason: str = "No reason provided"):
        mod_data = load_json(DATA_FILE)
        gid = str(ctx.guild.id)
        if gid in mod_data and "hardbans" in mod_data[gid]:
            for hb in mod_data[gid]["hardbans"]:
                if hb["user_id"] == user_id:
                    if ctx.author.id != OWNER_ID:
                        return await ctx.send(embed=e("❌ Error", f"{ctx.author.mention}, this user was hard banned. Only the bot owner can unban them!", COLORS["error"], self.bot.user))
        
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=f"{reason} | By: {ctx.author}")
            add_mod_log(ctx.guild.id, "unban", user_id, ctx.author.id, reason)
            
            embed = e("✅ User Unbanned", f"**User:** {user.mention}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}", COLORS["success"], self.bot.user)
            await ctx.send(embed=embed)
        except discord.NotFound:
            await ctx.send(embed=e("❌ Error", f"{ctx.author.mention}, user not found or not banned!", COLORS["error"], self.bot.user))

    @commands.command()
    @is_admin()
    async def massban(self, ctx, *members: discord.Member):
        if len(members) == 0:
            return await ctx.send(embed=e("❌ Error", f"{ctx.author.mention}, please provide members to ban!", COLORS["error"], self.bot.user))
        
        if len(members) > 10:
            return await ctx.send(embed=e("❌ Error", f"{ctx.author.mention}, you can only massban up to 10 users at once!", COLORS["error"], self.bot.user))
        
        banned = []
        failed = []
        
        for member in members:
            try:
                if member.top_role >= ctx.author.top_role and ctx.author.id != OWNER_ID:
                    failed.append(str(member))
                    continue
                await member.ban(reason=f"Massban by {ctx.author}")
                add_mod_log(ctx.guild.id, "massban", member.id, ctx.author.id, "Massban")
                banned.append(str(member))
            except:
                failed.append(str(member))
        
        embed = e("🔨 Massban Complete", f"**Banned:** {len(banned)}\n**Failed:** {len(failed)}", COLORS["success"], self.bot.user)
        if banned:
            embed.add_field(name="✅ Banned Users", value="\n".join(banned), inline=False)
        if failed:
            embed.add_field(name="❌ Failed", value="\n".join(failed), inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @is_mod()
    async def timeout(self, ctx, member: discord.Member, duration: str, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role and ctx.author.id != OWNER_ID:
            return await ctx.send(embed=e("❌ Error", f"{ctx.author.mention}, you cannot timeout someone with a higher or equal role!", COLORS["error"], self.bot.user))
        
        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        unit = duration[-1].lower()
        if unit not in time_units:
            return await ctx.send(embed=e("❌ Error", f"{ctx.author.mention}, invalid duration! Use s/m/h/d (e.g., 30m, 1h, 1d)", COLORS["error"], self.bot.user))
        
        try:
            amount = int(duration[:-1])
            seconds = amount * time_units[unit]
            if seconds > 2419200:
                return await ctx.send(embed=e("❌ Error", f"{ctx.author.mention}, timeout cannot exceed 28 days!", COLORS["error"], self.bot.user))
            
            until = datetime.utcnow() + timedelta(seconds=seconds)
            await member.timeout(until, reason=f"{reason} | By: {ctx.author}")
            add_mod_log(ctx.guild.id, "timeout", member.id, ctx.author.id, reason, duration)
            
            guild_settings = get_guild_settings(ctx.guild.id)
            if guild_settings.get("dm_on_action"):
                dm_embed = e("⏰ Timed Out", f"You have been timed out in **{ctx.guild.name}**\n\n**Duration:** {duration}\n**Reason:** {reason}\n**Moderator:** {ctx.author.mention}", bot_user=self.bot.user)
                await send_dm(member, dm_embed)
            
            embed = e("⏰ Member Timed Out", f"**User:** {member.mention}\n**Duration:** {duration}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}", COLORS["success"], self.bot.user)
            await ctx.send(embed=embed)
            
            log_embed = e("⏰ Member Timed Out", f"**User:** {member} ({member.id})\n**Duration:** {duration}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}", bot_user=self.bot.user)
            await log_action(ctx.guild, log_embed)
        except ValueError:
            await ctx.send(embed=e("❌ Error", f"{ctx.author.mention}, invalid duration format!", COLORS["error"], self.bot.user))

    @commands.command()
    @is_mod()
    async def untimeout(self, ctx, member: discord.Member):
        await member.timeout(None, reason=f"Timeout removed by {ctx.author}")
        add_mod_log(ctx.guild.id, "untimeout", member.id, ctx.author.id)
        
        embed = e("✅ Timeout Removed", f"**User:** {member.mention}\n**Moderator:** {ctx.author.mention}", COLORS["success"], self.bot.user)
        await ctx.send(embed=embed)

    @commands.command()
    @is_mod()
    async def nickname(self, ctx, member: discord.Member, *, new_nick: str = None):
        old_nick = member.display_name
        await member.edit(nick=new_nick)
        add_mod_log(ctx.guild.id, "nickname", member.id, ctx.author.id, f"Changed from '{old_nick}' to '{new_nick or 'Reset'}'")
        
        if new_nick:
            embed = e("✏️ Nickname Changed", f"**User:** {member.mention}\n**Old:** {old_nick}\n**New:** {new_nick}\n**Moderator:** {ctx.author.mention}", COLORS["success"], self.bot.user)
        else:
            embed = e("✏️ Nickname Reset", f"**User:** {member.mention}\n**Moderator:** {ctx.author.mention}", COLORS["success"], self.bot.user)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))