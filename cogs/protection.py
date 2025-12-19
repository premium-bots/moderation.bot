import discord
from discord.ext import commands
from utils import *

class Protection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @is_admin()
    async def protect(self, ctx, *, role: discord.Role):
        settings_data = load_json(SETTINGS_FILE)
        guild_settings = get_guild_settings(ctx.guild.id)
        if role.id not in guild_settings["protected_roles"]:
            guild_settings["protected_roles"].append(role.id)
            settings_data[str(ctx.guild.id)] = guild_settings
            save_json(SETTINGS_FILE, settings_data)
            embed = success_embed(f"Protected {role.mention} from moderation")
        else:
            guild_settings["protected_roles"].remove(role.id)
            settings_data[str(ctx.guild.id)] = guild_settings
            save_json(SETTINGS_FILE, settings_data)
            embed = info_embed(f"Removed protection from {role.mention}")
        
        await ctx.send(embed=embed)

    @commands.command()
    @is_admin()
    async def antinuke(self, ctx):
        settings_data = load_json(SETTINGS_FILE)
        guild_settings = get_guild_settings(ctx.guild.id)
        guild_settings["antinuke_enabled"] = not guild_settings.get("antinuke_enabled", False)
        settings_data[str(ctx.guild.id)] = guild_settings
        save_json(SETTINGS_FILE, settings_data)
        
        status = "enabled" if guild_settings["antinuke_enabled"] else "disabled"
        emoji = EMOJIS['check'] if guild_settings["antinuke_enabled"] else EMOJIS['deny']
        embed = create_embed(f"{emoji} Anti-nuke **{status}**", "success" if guild_settings["antinuke_enabled"] else "neutral")
        await ctx.send(embed=embed)

    @commands.command()
    @is_admin()
    async def antiraid(self, ctx):
        settings_data = load_json(SETTINGS_FILE)
        guild_settings = get_guild_settings(ctx.guild.id)
        guild_settings["antiraid_enabled"] = not guild_settings.get("antiraid_enabled", False)
        settings_data[str(ctx.guild.id)] = guild_settings
        save_json(SETTINGS_FILE, settings_data)
        
        status = "enabled" if guild_settings["antiraid_enabled"] else "disabled"
        emoji = EMOJIS['check'] if guild_settings["antiraid_enabled"] else EMOJIS['deny']
        embed = create_embed(f"{emoji} Anti-raid **{status}**", "success" if guild_settings["antiraid_enabled"] else "neutral")
        await ctx.send(embed=embed)

    @commands.command()
    @is_admin()
    async def antispam(self, ctx):
        settings_data = load_json(SETTINGS_FILE)
        guild_settings = get_guild_settings(ctx.guild.id)
        guild_settings["antispam_enabled"] = not guild_settings.get("antispam_enabled", False)
        settings_data[str(ctx.guild.id)] = guild_settings
        save_json(SETTINGS_FILE, settings_data)
        
        status = "enabled" if guild_settings["antispam_enabled"] else "disabled"
        emoji = EMOJIS['check'] if guild_settings["antispam_enabled"] else EMOJIS['deny']
        embed = create_embed(f"{emoji} Anti-spam **{status}**", "success" if guild_settings["antispam_enabled"] else "neutral")
        await ctx.send(embed=embed)

    @commands.command()
    @is_admin()
    async def automod(self, ctx):
        settings_data = load_json(SETTINGS_FILE)
        guild_settings = get_guild_settings(ctx.guild.id)
        guild_settings["automod_enabled"] = not guild_settings.get("automod_enabled", False)
        settings_data[str(ctx.guild.id)] = guild_settings
        save_json(SETTINGS_FILE, settings_data)
        
        status = "enabled" if guild_settings["automod_enabled"] else "disabled"
        emoji = EMOJIS['check'] if guild_settings["automod_enabled"] else EMOJIS['deny']
        embed = create_embed(f"{emoji} Auto-mod **{status}**", "success" if guild_settings["automod_enabled"] else "neutral")
        await ctx.send(embed=embed)

    @commands.command()
    @is_admin()
    async def vanityprotect(self, ctx):
        settings_data = load_json(SETTINGS_FILE)
        guild_settings = get_guild_settings(ctx.guild.id)
        guild_settings["vanity_protection"] = not guild_settings.get("vanity_protection", False)
        settings_data[str(ctx.guild.id)] = guild_settings
        save_json(SETTINGS_FILE, settings_data)
        
        status = "enabled" if guild_settings["vanity_protection"] else "disabled"
        emoji = EMOJIS['check'] if guild_settings["vanity_protection"] else EMOJIS['deny']
        embed = create_embed(f"{emoji} Vanity protection **{status}**", "success" if guild_settings["vanity_protection"] else "neutral")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Protection(bot))
