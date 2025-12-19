import discord
from discord.ext import commands
from discord import ui
import asyncio
from utils import *

class ConfirmView(ui.View):
    def __init__(self, ctx, action_name):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.action_name = action_name
        self.confirmed = False

    @ui.button(label="Confirm", style=discord.ButtonStyle.danger, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't for you!", ephemeral=True)
            return
        self.confirmed = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't for you!", ephemeral=True)
            return
        self.confirmed = False
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

class ChannelManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @is_mod()
    async def cleanup(self, ctx, amount: int = 50):
        if amount > 500:
            amount = 500
        
        deleted = await ctx.channel.purge(limit=amount, check=lambda m: m.author.bot)
        embed = e("🧹 Cleanup Complete", f"Deleted **{len(deleted)}** bot messages.\n**Moderator:** {ctx.author.mention}", COLORS["success"], self.bot.user)
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await msg.delete()

    @commands.command()
    @is_mod()
    async def purge(self, ctx, amount: int):
        if amount > 500:
            amount = 500
        if amount < 1:
            return await ctx.send(embed=e("❌ Error", f"{ctx.author.mention}, please provide a valid amount!", COLORS["error"], self.bot.user))
        
        deleted = await ctx.channel.purge(limit=amount + 1)
        add_mod_log(ctx.guild.id, "purge", ctx.channel.id, ctx.author.id, f"Deleted {len(deleted) - 1} messages")
        
        embed = e("🗑️ Messages Purged", f"Deleted **{len(deleted) - 1}** messages.\n**Moderator:** {ctx.author.mention}", COLORS["success"], self.bot.user)
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await msg.delete()

    @commands.command()
    async def selfpurge(self, ctx, amount: int = 50):
        if amount > 100:
            amount = 100
        
        deleted = await ctx.channel.purge(limit=amount, check=lambda m: m.author.id == ctx.author.id)
        embed = e("🗑️ Self-Purge Complete", f"Deleted **{len(deleted)}** of your messages.", COLORS["success"], self.bot.user)
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await msg.delete()

    @commands.command()
    @is_mod()
    async def lockdown(self, ctx, *, reason: str = "No reason provided"):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        add_mod_log(ctx.guild.id, "lockdown", ctx.channel.id, ctx.author.id, reason)
        
        embed = e("🔒 Channel Locked", f"This channel has been locked.\n\n**Reason:** {reason}\n**Moderator:** {ctx.author.mention}", COLORS["warning"], self.bot.user)
        await ctx.send(embed=embed)
        
        log_embed = e("🔒 Channel Locked", f"**Channel:** {ctx.channel.mention}\n**Reason:** {reason}\n**Moderator:** {ctx.author.mention}", bot_user=self.bot.user)
        await log_action(ctx.guild, log_embed)

    @commands.command()
    @is_mod()
    async def unlockdown(self, ctx):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        add_mod_log(ctx.guild.id, "unlockdown", ctx.channel.id, ctx.author.id)
        
        embed = e("🔓 Channel Unlocked", f"This channel has been unlocked.\n**Moderator:** {ctx.author.mention}", COLORS["success"], self.bot.user)
        await ctx.send(embed=embed)

    @commands.command()
    @is_mod()
    async def hide(self, ctx):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.view_channel = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        add_mod_log(ctx.guild.id, "hide", ctx.channel.id, ctx.author.id)
        
        embed = e("👁️ Channel Hidden", f"This channel is now hidden.\n**Moderator:** {ctx.author.mention}", COLORS["success"], self.bot.user)
        await ctx.send(embed=embed)

    @commands.command()
    @is_mod()
    async def reveal(self, ctx):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.view_channel = None
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        add_mod_log(ctx.guild.id, "reveal", ctx.channel.id, ctx.author.id)
        
        embed = e("👁️ Channel Revealed", f"This channel is now visible.\n**Moderator:** {ctx.author.mention}", COLORS["success"], self.bot.user)
        await ctx.send(embed=embed)

    @commands.command()
    @is_mod()
    async def slowmode(self, ctx, seconds: int):
        if seconds < 0 or seconds > 21600:
            return await ctx.send(embed=e("❌ Error", f"{ctx.author.mention}, slowmode must be between 0 and 21600 seconds!", COLORS["error"], self.bot.user))
        
        await ctx.channel.edit(slowmode_delay=seconds)
        add_mod_log(ctx.guild.id, "slowmode", ctx.channel.id, ctx.author.id, f"Set to {seconds}s")
        
        if seconds == 0:
            embed = e("⏱️ Slowmode Disabled", f"Slowmode has been disabled.\n**Moderator:** {ctx.author.mention}", COLORS["success"], self.bot.user)
        else:
            embed = e("⏱️ Slowmode Set", f"Slowmode set to **{seconds} seconds**.\n**Moderator:** {ctx.author.mention}", COLORS["success"], self.bot.user)
        await ctx.send(embed=embed)

    @commands.command()
    @is_admin()
    async def nsfw(self, ctx):
        new_state = not ctx.channel.is_nsfw()
        await ctx.channel.edit(nsfw=new_state)
        add_mod_log(ctx.guild.id, "nsfw", ctx.channel.id, ctx.author.id, f"Set to {new_state}")
        
        status = "enabled" if new_state else "disabled"
        embed = e(f"🔞 NSFW {status.title()}", f"NSFW has been {status} for this channel.\n**Moderator:** {ctx.author.mention}", COLORS["success"], self.bot.user)
        await ctx.send(embed=embed)

    @commands.command()
    @is_mod()
    async def topic(self, ctx, *, new_topic: str):
        await ctx.channel.edit(topic=new_topic)
        add_mod_log(ctx.guild.id, "topic", ctx.channel.id, ctx.author.id, new_topic)
        
        embed = e("📝 Topic Updated", f"**New Topic:** {new_topic}\n**Moderator:** {ctx.author.mention}", COLORS["success"], self.bot.user)
        await ctx.send(embed=embed)

    @commands.command()
    @is_admin()
    async def nuke(self, ctx):
        view = ConfirmView(ctx, "nuke this channel")
        embed = e("⚠️ Confirm Channel Nuke", f"{ctx.author.mention}, are you sure you want to nuke this channel?\n\nThis will delete and recreate the channel, removing all messages.", COLORS["warning"], self.bot.user)
        msg = await ctx.send(embed=embed, view=view)
        
        await view.wait()
        
        if view.confirmed:
            channel = ctx.channel
            position = channel.position
            
            new_channel = await channel.clone()
            await new_channel.edit(position=position)
            await channel.delete(reason=f"Channel nuked by {ctx.author}")
            
            add_mod_log(ctx.guild.id, "nuke", new_channel.id, ctx.author.id)
            
            embed = e("💥 Channel Nuked", f"This channel has been nuked by {ctx.author.mention}", COLORS["success"], self.bot.user)
            await new_channel.send(embed=embed)

    @commands.command()
    @is_mod()
    async def pin(self, ctx, message_id: int):
        try:
            message = await ctx.channel.fetch_message(message_id)
            await message.pin()
            embed = e("📌 Message Pinned", f"Message has been pinned.\n**Moderator:** {ctx.author.mention}", COLORS["success"], self.bot.user)
            await ctx.send(embed=embed)
        except:
            await ctx.send(embed=e("❌ Error", f"{ctx.author.mention}, message not found!", COLORS["error"], self.bot.user))

    @commands.command()
    @is_mod()
    async def unpin(self, ctx, message_id: int):
        try:
            message = await ctx.channel.fetch_message(message_id)
            await message.unpin()
            embed = e("📌 Message Unpinned", f"Message has been unpinned.\n**Moderator:** {ctx.author.mention}", COLORS["success"], self.bot.user)
            await ctx.send(embed=embed)
        except:
            await ctx.send(embed=e("❌ Error", f"{ctx.author.mention}, message not found!", COLORS["error"], self.bot.user))

async def setup(bot):
    await bot.add_cog(ChannelManagement(bot))