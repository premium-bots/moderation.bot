import discord
from discord.ext import commands
from discord import ui
from datetime import datetime
from utils import *

class ConfirmView(ui.View):
    def __init__(self, ctx, action_name):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.action_name = action_name
        self.confirmed = False

    @ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(embed=error_embed("This isn't for you."), ephemeral=True)
            return
        self.confirmed = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(embed=error_embed("This isn't for you."), ephemeral=True)
            return
        self.confirmed = False
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

class AdvancedModeration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @is_mod()
    async def warn(self, ctx, member: discord.Member, *, reason: str):
        if member.bot:
            return await ctx.send(embed=error_embed("You cannot warn bots."))
        
        warn_count = add_warning(ctx.guild.id, member.id, ctx.author.id, reason)
        add_mod_log(ctx.guild.id, "warn", member.id, ctx.author.id, reason)
        
        guild_settings = get_guild_settings(ctx.guild.id)
        max_warns = guild_settings.get("max_warnings", 5)
        
        if guild_settings.get("dm_on_action"):
            dm_embed = create_embed(
                f"You received a warning in **{ctx.guild.name}**\n```Warning: {warn_count}/{max_warns}\nReason: {reason}```",
                "warning"
            )
            await send_dm(member, dm_embed)
        
        embed = create_embed(f"{EMOJIS['check']} Warned **{member}**\n```Warning: {warn_count}/{max_warns}\nReason: {reason}```", "warning")
        await ctx.send(embed=embed)
        
        if warn_count >= max_warns:
            embed2 = create_embed(f"{EMOJIS['deny']} {member.mention} has reached maximum warnings ({max_warns})", "error")
            await ctx.send(embed=embed2)
        
        log_embed = info_embed(f"**User Warned**\n```User: {member} ({member.id})\nWarning: {warn_count}\nReason: {reason}\nModerator: {ctx.author}```")
        await log_action(ctx.guild, log_embed)

    @commands.command()
    @is_mod()
    async def warnings(self, ctx, member: discord.Member):
        warns = get_warnings(ctx.guild.id, member.id)
        
        if not warns:
            return await ctx.send(embed=info_embed(f"**{member}** has no warnings."))
        
        warn_list = []
        for i, warn in enumerate(warns[-10:], 1):
            mod = ctx.guild.get_member(warn["moderator"])
            mod_name = mod.display_name if mod else f"Unknown"
            timestamp = warn.get("timestamp", "Unknown")[:10]
            warn_list.append(f"#{i} - {warn['reason']}\n     By: {mod_name} | {timestamp}")
        
        embed = info_embed(f"**Warnings for {member.display_name}**\n```Total: {len(warns)}\n\n{chr(10).join(warn_list)}```")
        await ctx.send(embed=embed)

    @commands.command()
    @is_admin()
    async def clearwarnings(self, ctx, member: discord.Member):
        warnings_data = load_json(WARNINGS_FILE)
        gid = str(ctx.guild.id)
        uid = str(member.id)
        
        if gid in warnings_data and uid in warnings_data[gid]:
            count = len(warnings_data[gid][uid])
            warnings_data[gid][uid] = []
            save_json(WARNINGS_FILE, warnings_data)
            add_mod_log(ctx.guild.id, "clearwarnings", member.id, ctx.author.id, f"Cleared {count} warnings")
            
            embed = success_embed(f"Cleared **{count}** warnings from **{member}**")
        else:
            embed = info_embed(f"**{member}** has no warnings to clear.")
        
        await ctx.send(embed=embed)

    @commands.command()
    @is_mod()
    async def jail(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        guild_settings = get_guild_settings(ctx.guild.id)
        jail_role_id = guild_settings.get("jail_role")
        
        if not jail_role_id:
            return await ctx.send(embed=error_embed("Jail role not set. Use `em-setjailrole <role>`"))
        
        jail_role = ctx.guild.get_role(jail_role_id)
        if not jail_role:
            return await ctx.send(embed=error_embed("Jail role not found."))
        
        if member.top_role >= ctx.author.top_role and ctx.author.id != OWNER_ID:
            return await ctx.send(embed=error_embed("You cannot jail someone with a higher or equal role."))
        
        jail_data = load_json(JAIL_FILE)
        gid = str(ctx.guild.id)
        if gid not in jail_data:
            jail_data[gid] = {}
        
        jail_data[gid][str(member.id)] = {
            "roles": [r.id for r in member.roles if r != ctx.guild.default_role],
            "reason": reason,
            "moderator": ctx.author.id,
            "timestamp": datetime.utcnow().isoformat()
        }
        save_json(JAIL_FILE, jail_data)
        
        roles_to_remove = [r for r in member.roles if r != ctx.guild.default_role and r < ctx.guild.me.top_role]
        await member.remove_roles(*roles_to_remove, reason=f"Jailed by {ctx.author}")
        await member.add_roles(jail_role, reason=f"Jailed by {ctx.author}")
        add_mod_log(ctx.guild.id, "jail", member.id, ctx.author.id, reason)
        
        if guild_settings.get("dm_on_action"):
            dm_embed = create_embed(
                f"You have been jailed in **{ctx.guild.name}**\n```Reason: {reason}```",
                "error"
            )
            await send_dm(member, dm_embed)
        
        embed = success_embed(f"Jailed **{member}**\n```Reason: {reason}```")
        await ctx.send(embed=embed)
        
        log_embed = info_embed(f"**User Jailed**\n```User: {member} ({member.id})\nReason: {reason}\nModerator: {ctx.author}```")
        await log_action(ctx.guild, log_embed)

    @commands.command()
    @is_mod()
    async def unjail(self, ctx, member: discord.Member):
        guild_settings = get_guild_settings(ctx.guild.id)
        jail_role_id = guild_settings.get("jail_role")
        
        jail_data = load_json(JAIL_FILE)
        gid = str(ctx.guild.id)
        uid = str(member.id)
        
        if gid not in jail_data or uid not in jail_data[gid]:
            return await ctx.send(embed=error_embed("This user is not jailed."))
        
        jail_info = jail_data[gid][uid]
        saved_roles = [ctx.guild.get_role(rid) for rid in jail_info.get("roles", [])]
        saved_roles = [r for r in saved_roles if r and r < ctx.guild.me.top_role]
        
        if jail_role_id:
            jail_role = ctx.guild.get_role(jail_role_id)
            if jail_role and jail_role in member.roles:
                await member.remove_roles(jail_role, reason=f"Unjailed by {ctx.author}")
        
        if saved_roles:
            await member.add_roles(*saved_roles, reason=f"Unjailed by {ctx.author}")
        
        del jail_data[gid][uid]
        save_json(JAIL_FILE, jail_data)
        add_mod_log(ctx.guild.id, "unjail", member.id, ctx.author.id)
        
        embed = success_embed(f"Unjailed **{member}**\n```Roles Restored: {len(saved_roles)}```")
        await ctx.send(embed=embed)

    @commands.command()
    @is_mod()
    async def jailed(self, ctx):
        jail_data = load_json(JAIL_FILE)
        gid = str(ctx.guild.id)
        
        if gid not in jail_data or not jail_data[gid]:
            return await ctx.send(embed=info_embed("No users are currently jailed."))
        
        jailed_list = []
        for uid, info in list(jail_data[gid].items())[:25]:
            member = ctx.guild.get_member(int(uid))
            member_name = member.display_name if member else f"Unknown ({uid})"
            mod = ctx.guild.get_member(info.get("moderator"))
            mod_name = mod.display_name if mod else "Unknown"
            jailed_list.append(f"{member_name}\n  Reason: {info.get('reason', 'N/A')}\n  By: {mod_name}")
        
        embed = info_embed(f"**Jailed Users** ({len(jail_data[gid])})\n```{chr(10).join(jailed_list)}```")
        await ctx.send(embed=embed)

    @commands.command()
    @is_mod()
    async def imute(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role and ctx.author.id != OWNER_ID:
            return await ctx.send(embed=error_embed("You cannot mute someone with a higher or equal role."))
        
        overwrite = ctx.channel.overwrites_for(member)
        overwrite.attach_files = False
        overwrite.embed_links = False
        await ctx.channel.set_permissions(member, overwrite=overwrite)
        add_mod_log(ctx.guild.id, "imute", member.id, ctx.author.id, reason)
        
        embed = success_embed(f"Image muted **{member}**\n```Reason: {reason}\nChannel: {ctx.channel.name}```")
        await ctx.send(embed=embed)

    @commands.command()
    @is_mod()
    async def rmute(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role and ctx.author.id != OWNER_ID:
            return await ctx.send(embed=error_embed("You cannot mute someone with a higher or equal role."))
        
        overwrite = ctx.channel.overwrites_for(member)
        overwrite.add_reactions = False
        await ctx.channel.set_permissions(member, overwrite=overwrite)
        add_mod_log(ctx.guild.id, "rmute", member.id, ctx.author.id, reason)
        
        embed = success_embed(f"Reaction muted **{member}**\n```Reason: {reason}\nChannel: {ctx.channel.name}```")
        await ctx.send(embed=embed)

    @commands.command()
    @is_mod()
    async def modhistory(self, ctx, member: discord.Member):
        history = get_mod_history(ctx.guild.id, member.id)
        
        if not history:
            return await ctx.send(embed=info_embed(f"**{member}** has no moderation history."))
        
        history_list = []
        for log in history[-10:]:
            mod = ctx.guild.get_member(int(log.get("moderator")))
            mod_name = mod.display_name if mod else "Unknown"
            action = log.get("action", "unknown").upper()
            reason = log.get("reason", "N/A")
            timestamp = log.get("timestamp", "Unknown")[:10]
            history_list.append(f"{action} | {timestamp}\n  By: {mod_name}\n  Reason: {reason}")
        
        embed = info_embed(f"**Moderation History for {member.display_name}**\n```Total Actions: {len(history)}\n\n{chr(10).join(history_list)}```")
        await ctx.send(embed=embed)

    @commands.command()
    @is_mod()
    async def history(self, ctx, member: discord.Member):
        await self.modhistory(ctx, member=member)

    @commands.command()
    @is_mod()
    async def drag(self, ctx, member: discord.Member, channel: discord.VoiceChannel):
        if not member.voice:
            return await ctx.send(embed=error_embed(f"**{member}** is not in a voice channel."))
        
        await member.move_to(channel, reason=f"Dragged by {ctx.author}")
        add_mod_log(ctx.guild.id, "drag", member.id, ctx.author.id, f"Moved to {channel.name}")
        
        embed = success_embed(f"Moved **{member}** to **{channel.name}**")
        await ctx.send(embed=embed)

    @commands.command()
    @is_mod()
    async def moveall(self, ctx, from_channel: discord.VoiceChannel, to_channel: discord.VoiceChannel):
        if not from_channel.members:
            return await ctx.send(embed=error_embed(f"No members in **{from_channel.name}**"))
        
        moved = 0
        for member in from_channel.members:
            try:
                await member.move_to(to_channel, reason=f"Mass move by {ctx.author}")
                moved += 1
            except:
                pass
        
        add_mod_log(ctx.guild.id, "moveall", from_channel.id, ctx.author.id, f"Moved {moved} users to {to_channel.name}")
        
        embed = success_embed(f"Moved **{moved}** users\n```From: {from_channel.name}\nTo: {to_channel.name}```")
        await ctx.send(embed=embed)

    @commands.command()
    @is_mod()
    async def newusers(self, ctx, count: int = 10):
        if count > 25:
            count = 25
        
        members = sorted(ctx.guild.members, key=lambda m: m.joined_at or datetime.min, reverse=True)[:count]
        
        user_list = []
        for i, member in enumerate(members, 1):
            joined = member.joined_at.strftime("%Y-%m-%d %H:%M") if member.joined_at else "Unknown"
            user_list.append(f"{i}. {member.display_name}\n   Joined: {joined}")
        
        embed = info_embed(f"**New Users** ({count})\n```{chr(10).join(user_list)}```")
        await ctx.send(embed=embed)

    @commands.command()
    @is_admin()
    async def audit(self, ctx, action: str = None):
        try:
            entries = []
            async for entry in ctx.guild.audit_logs(limit=10):
                entries.append(entry)
            
            audit_list = []
            for entry in entries:
                target = entry.target.name if hasattr(entry.target, 'name') else str(entry.target)
                audit_list.append(f"{entry.action.name}\n  By: {entry.user}\n  Target: {target}")
            
            embed = info_embed(f"**Audit Log** (Last {len(entries)})\n```{chr(10).join(audit_list)}```")
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send(embed=error_embed("I don't have permission to view audit logs."))

    @commands.command()
    @is_owner()
    async def chunkban(self, ctx, *, role: discord.Role):
        members_with_role = [m for m in ctx.guild.members if role in m.roles]
        
        if not members_with_role:
            return await ctx.send(embed=error_embed("No members have this role."))
        
        view = ConfirmView(ctx, f"ban {len(members_with_role)} users")
        embed = create_embed(f"Are you sure you want to ban **{len(members_with_role)}** users with {role.mention}?", "warning")
        msg = await ctx.send(embed=embed, view=view)
        
        await view.wait()
        
        if view.confirmed:
            banned = 0
            failed = 0
            for member in members_with_role:
                try:
                    await member.ban(reason=f"Chunkban of role {role.name} by {ctx.author}")
                    banned += 1
                except:
                    failed += 1
            
            add_mod_log(ctx.guild.id, "chunkban", role.id, ctx.author.id, f"Banned {banned} users")
            
            embed = success_embed(f"Chunkban complete\n```Banned: {banned}\nFailed: {failed}\nRole: {role.name}```")
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AdvancedModeration(bot))