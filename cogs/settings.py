import discord
from discord.ext import commands
from discord import ui
from utils import *

class SettingsView(ui.View):
    def __init__(self, ctx, guild_settings, bot):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.guild_settings = guild_settings
        self.bot = bot

    def get_embed(self):
        gs = self.guild_settings
        
        # Channels & Roles
        log_ch = f"<#{gs['log_channel']}>" if gs.get('log_channel') else "Not set"
        jail_role = f"<@&{gs['jail_role']}>" if gs.get('jail_role') else "Not set"
        mute_role = f"<@&{gs['mute_role']}>" if gs.get('mute_role') else "Not set"
        
        # Role lists
        mod_roles = ", ".join([f"<@&{r}>" for r in gs.get('mod_roles', [])]) or "None"
        admin_roles = ", ".join([f"<@&{r}>" for r in gs.get('admin_roles', [])]) or "None"
        protected = ", ".join([f"<@&{r}>" for r in gs.get('protected_roles', [])]) or "None"
        
        # Status indicators
        status = lambda x: f"{EMOJIS['check']}" if x else f"{EMOJIS['deny']}"
        
        settings_text = f"""
Log Channel: {log_ch}
Jail Role: {jail_role}
Mute Role: {mute_role}

Mod Roles: {mod_roles}
Admin Roles: {admin_roles}
Protected: {protected}

{status(gs.get('automod_enabled'))} Auto-Mod
{status(gs.get('antispam_enabled'))} Anti-Spam
{status(gs.get('antiraid_enabled'))} Anti-Raid
{status(gs.get('antinuke_enabled'))} Anti-Nuke
{status(gs.get('dm_on_action'))} DM on Action
Max Warnings: {gs.get('max_warnings', 5)}
        """
        
        embed = discord.Embed(
            title=f"Settings for {self.ctx.guild.name}",
            description=settings_text.strip(),
            color=COLORS["info"]
        )
        
        return embed

    @ui.button(label="Refresh", style=discord.ButtonStyle.secondary)
    async def refresh(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(embed=error_embed("This menu isn't for you."), ephemeral=True)
            return
        self.guild_settings = get_guild_settings(self.ctx.guild.id)
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @is_admin()
    async def settings(self, ctx):
        guild_settings = get_guild_settings(ctx.guild.id)
        view = SettingsView(ctx, guild_settings, self.bot)
        await ctx.send(embed=view.get_embed(), view=view)

    @commands.command()
    @is_admin()
    async def setlog(self, ctx, channel: discord.TextChannel):
        settings_data = load_json(SETTINGS_FILE)
        guild_settings = get_guild_settings(ctx.guild.id)
        guild_settings["log_channel"] = channel.id
        settings_data[str(ctx.guild.id)] = guild_settings
        save_json(SETTINGS_FILE, settings_data)
        
        embed = success_embed(f"Log channel set to {channel.mention}")
        await ctx.send(embed=embed)

    @commands.command()
    @is_admin()
    async def setjailrole(self, ctx, *, role: discord.Role):
        settings_data = load_json(SETTINGS_FILE)
        guild_settings = get_guild_settings(ctx.guild.id)
        guild_settings["jail_role"] = role.id
        settings_data[str(ctx.guild.id)] = guild_settings
        save_json(SETTINGS_FILE, settings_data)
        
        embed = success_embed(f"Jail role set to {role.mention}")
        await ctx.send(embed=embed)

    @commands.command()
    @is_admin()
    async def setmuterole(self, ctx, *, role: discord.Role):
        settings_data = load_json(SETTINGS_FILE)
        guild_settings = get_guild_settings(ctx.guild.id)
        guild_settings["mute_role"] = role.id
        settings_data[str(ctx.guild.id)] = guild_settings
        save_json(SETTINGS_FILE, settings_data)
        
        embed = success_embed(f"Mute role set to {role.mention}")
        await ctx.send(embed=embed)

    @commands.command()
    @is_admin()
    async def addmodrole(self, ctx, *, role: discord.Role):
        settings_data = load_json(SETTINGS_FILE)
        guild_settings = get_guild_settings(ctx.guild.id)
        if role.id not in guild_settings["mod_roles"]:
            guild_settings["mod_roles"].append(role.id)
            settings_data[str(ctx.guild.id)] = guild_settings
            save_json(SETTINGS_FILE, settings_data)
            embed = success_embed(f"Added {role.mention} as moderator role")
        else:
            embed = info_embed(f"{role.mention} is already a moderator role")
        
        await ctx.send(embed=embed)

    @commands.command()
    @is_admin()
    async def addadminrole(self, ctx, *, role: discord.Role):
        settings_data = load_json(SETTINGS_FILE)
        guild_settings = get_guild_settings(ctx.guild.id)
        if role.id not in guild_settings["admin_roles"]:
            guild_settings["admin_roles"].append(role.id)
            settings_data[str(ctx.guild.id)] = guild_settings
            save_json(SETTINGS_FILE, settings_data)
            embed = success_embed(f"Added {role.mention} as admin role")
        else:
            embed = info_embed(f"{role.mention} is already an admin role")
        
        await ctx.send(embed=embed)

    @commands.command()
    @is_mod()
    async def banlist(self, ctx):
        try:
            bans = [ban async for ban in ctx.guild.bans(limit=50)]
            
            if not bans:
                return await ctx.send(embed=info_embed("No banned users."))
            
            ban_list = []
            for ban in bans[:25]:
                reason = ban.reason or "No reason"
                ban_list.append(f"{ban.user} ({ban.user.id})\n  {reason}")
            
            embed = info_embed(f"**Ban List** ({len(bans)} total)\n```{chr(10).join(ban_list)}```")
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send(embed=error_embed("I don't have permission to view bans."))

    @commands.command()
    @is_owner()
    async def hardbanlist(self, ctx):
        mod_data = load_json(DATA_FILE)
        gid = str(ctx.guild.id)
        
        if gid not in mod_data or "hardbans" not in mod_data[gid] or not mod_data[gid]["hardbans"]:
            return await ctx.send(embed=info_embed("No permanently banned users."))
        
        hardbans = mod_data[gid]["hardbans"]
        
        hb_list = []
        for hb in hardbans[:25]:
            mod = ctx.guild.get_member(hb.get("moderator"))
            mod_name = mod.display_name if mod else "Unknown"
            timestamp = hb.get('timestamp', 'Unknown')[:10]
            hb_list.append(f"{hb.get('username', 'Unknown')} ({hb.get('user_id')})\n  Reason: {hb.get('reason', 'N/A')}\n  By: {mod_name} | {timestamp}")
        
        embed = create_embed(f"{EMOJIS['crown']} **Hardban List** ({len(hardbans)})\n```{chr(10).join(hb_list)}```", "error")
        await ctx.send(embed=embed)

    @commands.command()
    @is_mod()
    async def mutelist(self, ctx):
        guild_settings = get_guild_settings(ctx.guild.id)
        mute_role_id = guild_settings.get("mute_role")
        
        if not mute_role_id:
            return await ctx.send(embed=error_embed("Mute role not set."))
        
        mute_role = ctx.guild.get_role(mute_role_id)
        if not mute_role:
            return await ctx.send(embed=error_embed("Mute role not found."))
        
        muted_members = [m for m in ctx.guild.members if mute_role in m.roles]
        
        if not muted_members:
            return await ctx.send(embed=info_embed("No muted users."))
        
        mute_list = [f"{m.display_name} ({m.id})" for m in muted_members[:25]]
        
        embed = info_embed(f"**Muted Users** ({len(muted_members)})\n```{chr(10).join(mute_list)}```")
        await ctx.send(embed=embed)

    @commands.command()
    @is_admin()
    async def setup(self, ctx):
        setup_text = """
em-setlog <channel>      Set log channel
em-setjailrole <role>    Set jail role
em-setmuterole <role>    Set mute role
em-addmodrole <role>     Add mod role
em-addadminrole <role>   Add admin role
em-protect <role>        Protect role

Protection Features:
em-antinuke     Toggle anti-nuke
em-antiraid     Toggle anti-raid
em-antispam     Toggle anti-spam
em-automod      Toggle auto-mod
        """
        
        embed = discord.Embed(
            title="Bot Setup",
            description=f"```{setup_text.strip()}```",
            color=COLORS["info"]
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Settings(bot))