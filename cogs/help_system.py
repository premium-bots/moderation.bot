# cogs/help_system.py
import discord
from discord.ext import commands
from discord import ui
from utils import *

class HelpView(ui.View):
    def __init__(self, ctx, bot):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.bot = bot
        self.page = "main"

    def get_main_embed(self):
        embed = discord.Embed(
            title=f"{self.bot.user.name} Command Help",
            color=COLORS["info"]
        )
        
        # Left side: Information
        embed.add_field(
            name="Information",
            value="> **Prefix:** `em-`\n> **Categories:** `6`\n> **Commands:** `{}`".format(len(self.bot.commands)),
            inline=True
        )
        
        # Right side: Links (empty for now, but matches layout)
        embed.add_field(
            name="Links",
            value="> [Website](https://harassment.lol)\n> [Support Server](https://discord.gg/invite/economy)",
            inline=True
        )
        
        # L
        
        # Footer hint
        embed.set_footer(text="If you need help with a specific command, use: em-help <command>")
        embed.set_thumbnail(url=self.ctx.guild.icon.url)
        
        # Optional: guild icon as thumbnail if you want, but Loti doesn't have it
        # if self.ctx.guild.icon:
        #     embed.set_thumbnail(url=self.ctx.guild.icon.url)
        
        return embed

    def get_category_embed(self, title: str, command_list: str):
        embed = discord.Embed(
            title=f"Category: {title}",
            description="Commands available in this category:",
            color=COLORS["info"]
        )
        
        embed.add_field(
            name="Commands",
            value=f"```{command_list}```",
            inline=False
        )
        
        total_commands = len([c for c in command_list.split(', ') if c.strip()])
        embed.add_field(name="Total", value=f"{total_commands} commands", inline=False)
        
        # Keep the festive image on category pages too (or remove if you prefer none)
        
        return embed

    def get_mod_embed(self):
        commands = "kick, ban, softban, hardban, unban, massban, timeout, untimeout, nickname"
        return self.get_category_embed("Moderation", commands)

    def get_channel_embed(self):
        commands = "cleanup, purge, selfpurge, lockdown, unlockdown, hide, reveal, slowmode, nsfw, topic, nuke, pin, unpin"
        return self.get_category_embed("Channel Management", commands)

    def get_role_embed(self):
        commands = "role, temprole, denyperm, strip, picperms"
        return self.get_category_embed("Role Management", commands)

    def get_advanced_embed(self):
        commands = "warn, warnings, clearwarnings, jail, unjail, jailed, modhistory, history, drag, moveall, newusers, audit, chunkban"
        return self.get_category_embed("Advanced Moderation", commands)

    def get_protection_embed(self):
        commands = "setup, protect, antinuke, antiraid, antispam, automod, vanityprotect"
        return self.get_category_embed("Protection", commands)

    def get_settings_embed(self):
        commands = "settings, setlog, setjailrole, setmuterole, addmodrole, addadminrole, banlist, hardbanlist, mutelist"
        return self.get_category_embed("Settings", commands)

    @ui.select(
        placeholder="Select a Category",
        options=[
            discord.SelectOption(label="Main Menu", value="main", description="Back to overview"),
            discord.SelectOption(label="Moderation", value="mod", description="Basic moderation tools"),
            discord.SelectOption(label="Channel Management", value="channel", description="Channel control commands"),
            discord.SelectOption(label="Role Management", value="role", description="Role assignment & management"),
            discord.SelectOption(label="Advanced Moderation", value="advanced", description="Warnings, jail, history"),
            discord.SelectOption(label="Protection", value="protection", description="Anti-raid/nuke features"),
            discord.SelectOption(label="Settings", value="settings", description="Bot configuration"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: ui.Select):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(embed=error_embed("This help menu isn't for you."), ephemeral=True)
            return

        self.page = select.values[0]
        embeds = {
            "main": self.get_main_embed,
            "mod": self.get_mod_embed,
            "channel": self.get_channel_embed,
            "role": self.get_role_embed,
            "advanced": self.get_advanced_embed,
            "protection": self.get_protection_embed,
            "settings": self.get_settings_embed
        }
        
        await interaction.response.edit_message(embed=embeds[self.page](), view=self)


class HelpSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["h", "commands"])
    async def help(self, ctx):
        view = HelpView(ctx, self.bot)
        await ctx.send(embed=view.get_main_embed(), view=view)


async def setup(bot):
    await bot.add_cog(HelpSystem(bot))