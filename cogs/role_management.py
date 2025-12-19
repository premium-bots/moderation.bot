import discord
from discord.ext import commands
import asyncio
from utils import *

class RoleManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @is_mod()
    async def role(self, ctx, member: discord.Member, *, role: discord.Role):
        if role >= ctx.author.top_role and ctx.author.id != OWNER_ID:
            return await ctx.send(embed=error_embed("You cannot assign a role higher than or equal to your own."))
        
        if role in member.roles:
            await member.remove_roles(role)
            add_mod_log(ctx.guild.id, "role_remove", member.id, ctx.author.id, f"Removed {role.name}")
            embed = success_embed(f"Removed {role.name} from **{member}**")
        else:
            await member.add_roles(role)
            add_mod_log(ctx.guild.id, "role_add", member.id, ctx.author.id, f"Added {role.name}")
            embed = success_embed(f"Added Role {role.name} to **{member}**")
        
        await ctx.send(embed=embed)

    @commands.command()
    @is_mod()
    async def temprole(self, ctx, member: discord.Member, role: discord.Role, duration: str):
        if role >= ctx.author.top_role and ctx.author.id != OWNER_ID:
            return await ctx.send(embed=error_embed("You cannot assign a role higher than or equal to your own."))
        
        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        unit = duration[-1].lower()
        if unit not in time_units:
            return await ctx.send(embed=error_embed("Invalid duration. Use: s/m/h/d"))
        
        try:
            amount = int(duration[:-1])
            seconds = amount * time_units[unit]
            
            await member.add_roles(role)
            add_mod_log(ctx.guild.id, "temprole", member.id, ctx.author.id, f"Added {role.name} for {duration}")
            
            embed = success_embed(f"Temporary role added to **{member}**\n```Role: {role.name}\nDuration: {duration}```")
            await ctx.send(embed=embed)
            
            await asyncio.sleep(seconds)
            
            if role in member.roles:
                await member.remove_roles(role)
                dm_embed = info_embed(f"Your temporary role **{role.name}** in **{ctx.guild.name}** has expired.")
                await send_dm(member, dm_embed)
        except ValueError:
            await ctx.send(embed=error_embed("Invalid duration format."))

    @commands.command()
    @is_admin()
    async def denyperm(self, ctx, member: discord.Member, permission: str):
        perm_name = permission.lower().replace(" ", "_")
        valid_perms = [
            "send_messages", "read_messages", "view_channel", "embed_links",
            "attach_files", "add_reactions", "use_external_emojis", "mention_everyone",
            "manage_messages", "read_message_history", "connect", "speak"
        ]
        
        if perm_name not in valid_perms:
            return await ctx.send(embed=error_embed(f"Invalid permission.\n```Valid: {', '.join(valid_perms)}```"))
        
        overwrite = ctx.channel.overwrites_for(member)
        setattr(overwrite, perm_name, False)
        await ctx.channel.set_permissions(member, overwrite=overwrite)
        add_mod_log(ctx.guild.id, "denyperm", member.id, ctx.author.id, f"Denied {perm_name}")
        
        embed = success_embed(f"Denied permission for **{member}**\n```Permission: {perm_name}\nChannel: {ctx.channel.name}```")
        await ctx.send(embed=embed)

    @commands.command()
    @is_admin()
    async def strip(self, ctx, member: discord.Member):
        if member.top_role >= ctx.author.top_role and ctx.author.id != OWNER_ID:
            return await ctx.send(embed=error_embed("You cannot strip roles from someone with a higher or equal role."))
        
        roles_to_remove = [r for r in member.roles if r != ctx.guild.default_role and r < ctx.guild.me.top_role]
        removed_count = len(roles_to_remove)
        
        await member.remove_roles(*roles_to_remove, reason=f"Roles stripped by {ctx.author}")
        add_mod_log(ctx.guild.id, "strip", member.id, ctx.author.id, f"Removed {removed_count} roles")
        
        embed = success_embed(f"Stripped all roles from **{member}**\n```Roles Removed: {removed_count}```")
        await ctx.send(embed=embed)

    @commands.command()
    @is_mod()
    async def picperms(self, ctx, *, role: discord.Role):
        perms = role.permissions
        enabled = []
        disabled = []
        
        for perm, value in perms:
            perm_name = perm.replace("_", " ").title()
            if value:
                enabled.append(perm_name)
        
        embed = info_embed(f"**Permissions for {role.name}**\n```{chr(10).join(enabled[:20]) if enabled else 'No permissions'}```")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RoleManagement(bot))