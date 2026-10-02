"""
BEN Discord Bot - Welcome & Leave System
Delivers high-impact transparent greeting cards and farewell notices with full customization.
"""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from utils.embeds import BenEmbed, success_embed, error_embed
import config

class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

    welcome_group = app_commands.Group(name="welcome", description="Manage the server welcome system")
    leave_group = app_commands.Group(name="leave", description="Manage the server leave / goodbye system")

    def format_message(self, template: str, member: discord.Member) -> str:
        """Interpolates variables inside custom welcome/leave templates."""
        return (
            template.replace("{user}", str(member))
            .replace("{name}", member.name)
            .replace("{mention}", member.mention)
            .replace("{server}", member.guild.name)
            .replace("{member_count}", str(member.guild.member_count))
        )

    def build_welcome_embed(self, member: discord.Member, custom_msg: Optional[str] = None) -> BenEmbed:
        guild = member.guild
        default_desc = (
            f"### Welcome to **{guild.name}**, {member.mention}! ✦\n"
            f"> We're delighted to have you join our community.\n\n"
            f"{config.EMOJIS['bullet']} **User**: `{member.name}` ({member.id})\n"
            f"{config.EMOJIS['bullet']} **Account Created**: <t:{int(member.created_at.timestamp())}:R>\n"
            f"{config.EMOJIS['bullet']} **Member Count**: `#{guild.member_count}`\n"
        )
        desc = self.format_message(custom_msg, member) if custom_msg else default_desc

        embed = BenEmbed(
            title=f"{config.EMOJIS['welcome']}  MEMBER ARRIVAL",
            description=desc,
            color=config.COLOR_TRANSPARENT,
            thumbnail=member.display_avatar.url,
            footer_text=f"{config.BOT_NAME} Security • Member #{guild.member_count}"
        )
        if guild.icon:
            embed.set_author(name=guild.name, icon_url=guild.icon.url)
        return embed

    def build_leave_embed(self, member: discord.Member, custom_msg: Optional[str] = None) -> BenEmbed:
        guild = member.guild
        default_desc = (
            f"### Farewell, **{member.name}**... 🚪\n"
            f"> A member has departed from **{guild.name}**.\n\n"
            f"{config.EMOJIS['bullet']} **Member**: `{member.name}` ({member.id})\n"
            f"{config.EMOJIS['bullet']} **Joined Server**: <t:{int(member.joined_at.timestamp()) if member.joined_at else 0}:R>\n"
            f"{config.EMOJIS['bullet']} **Remaining Members**: `{guild.member_count}`\n"
        )
        desc = self.format_message(custom_msg, member) if custom_msg else default_desc

        embed = BenEmbed(
            title=f"{config.EMOJIS['leave']}  MEMBER DEPARTURE",
            description=desc,
            color=config.COLOR_TRANSPARENT,
            thumbnail=member.display_avatar.url,
            footer_text=f"{config.BOT_NAME} Security • Member #{guild.member_count}"
        )
        return embed

    # --- Slash Commands for Welcome ---
    @welcome_group.command(name="setup", description="Configure the welcome greeting channel and optional message")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(
        channel="The text channel where welcome cards will be dispatched",
        message="Optional custom message. Variables: {user}, {mention}, {server}, {member_count}"
    )
    async def welcome_setup(self, interaction: discord.Interaction, channel: discord.TextChannel, message: Optional[str] = None):
        await self.db.update_guild_setting(interaction.guild_id, "welcome_channel_id", channel.id)
        if message:
            await self.db.update_guild_setting(interaction.guild_id, "welcome_message", message)
        await self.db.update_guild_setting(interaction.guild_id, "welcome_enabled", 1)

        embed = success_embed(
            "Welcome System Activated",
            f"Arrival announcements are now active.\n\n"
            f"{config.EMOJIS['bullet']} **Destination**: {channel.mention}\n"
            f"{config.EMOJIS['bullet']} **Custom Template**: `{message or 'Default High-Spec Design'}`\n"
            f"\n*Tip: Use `/welcome test` to preview your live welcome card!*"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @welcome_group.command(name="test", description="Send a test preview of your welcome card to the current channel")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def welcome_test(self, interaction: discord.Interaction):
        settings = await self.db.get_guild_settings(interaction.guild_id)
        msg_template = settings.get("welcome_message")
        embed = self.build_welcome_embed(interaction.user, msg_template)
        await interaction.response.send_message(
            content=f"✦ **Previewing Welcome Card:**",
            embed=embed,
            ephemeral=True
        )

    @welcome_group.command(name="toggle", description="Enable or disable the welcome system")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def welcome_toggle(self, interaction: discord.Interaction, enabled: bool):
        await self.db.update_guild_setting(interaction.guild_id, "welcome_enabled", 1 if enabled else 0)
        status = "enabled" if enabled else "disabled"
        await interaction.response.send_message(
            embed=success_embed("System Updated", f"The welcome system is now **{status}**."),
            ephemeral=True
        )

    # --- Slash Commands for Leave ---
    @leave_group.command(name="setup", description="Configure the leave/farewell channel and optional message")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(
        channel="The text channel where leave notices will be dispatched",
        message="Optional custom message. Variables: {user}, {name}, {server}, {member_count}"
    )
    async def leave_setup(self, interaction: discord.Interaction, channel: discord.TextChannel, message: Optional[str] = None):
        await self.db.update_guild_setting(interaction.guild_id, "leave_channel_id", channel.id)
        if message:
            await self.db.update_guild_setting(interaction.guild_id, "leave_message", message)
        await self.db.update_guild_setting(interaction.guild_id, "leave_enabled", 1)

        embed = success_embed(
            "Farewell System Activated",
            f"Departure notices are now active.\n\n"
            f"{config.EMOJIS['bullet']} **Destination**: {channel.mention}\n"
            f"{config.EMOJIS['bullet']} **Custom Template**: `{message or 'Default High-Spec Design'}`\n"
            f"\n*Tip: Use `/leave test` to preview your live farewell card!*"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @leave_group.command(name="test", description="Send a test preview of your farewell card to the current channel")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def leave_test(self, interaction: discord.Interaction):
        settings = await self.db.get_guild_settings(interaction.guild_id)
        msg_template = settings.get("leave_message")
        embed = self.build_leave_embed(interaction.user, msg_template)
        await interaction.response.send_message(
            content=f"✦ **Previewing Farewell Card:**",
            embed=embed,
            ephemeral=True
        )

    # --- Event Listeners ---
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return
        settings = await self.db.get_guild_settings(member.guild.id)
        if not settings.get("welcome_enabled", 1):
            return
        channel_id = settings.get("welcome_channel_id")
        if not channel_id:
            return
        channel = member.guild.get_channel(channel_id)
        if channel and channel.permissions_for(member.guild.me).send_messages:
            embed = self.build_welcome_embed(member, settings.get("welcome_message"))
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.bot:
            return
        settings = await self.db.get_guild_settings(member.guild.id)
        if not settings.get("leave_enabled", 1):
            return
        channel_id = settings.get("leave_channel_id")
        if not channel_id:
            return
        channel = member.guild.get_channel(channel_id)
        if channel and channel.permissions_for(member.guild.me).send_messages:
            embed = self.build_leave_embed(member, settings.get("leave_message"))
            await channel.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
