"""
BEN Discord Bot - Comprehensive Audit & Security Logging System
Records server events: message deletions/edits, member updates, role changes, and voice movements.
"""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from utils.embeds import BenEmbed, success_embed, error_embed
import config
class Logs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
    logs_group = app_commands.Group(name="logs", description="Configure audit log settings")
    async def get_log_channel(self, guild: discord.Guild) -> Optional[discord.TextChannel]:
        settings = await self.db.get_guild_settings(guild.id)
        if not settings.get("log_enabled", 1):
            return None
        channel_id = settings.get("log_channel_id")
        if not channel_id:
            return None
        channel = guild.get_channel(channel_id)
        if channel and channel.permissions_for(guild.me).send_messages:
            return channel
        return None
    @logs_group.command(name="setup", description="Designate the target channel for audit logging")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(channel="The channel where audit security logs will be routed")
    async def logs_setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.db.update_guild_setting(interaction.guild_id, "log_channel_id", channel.id)
        await self.db.update_guild_setting(interaction.guild_id, "log_enabled", 1)
        embed = success_embed(
            "Audit Logging Configured",
            f"Audit log events will now be recorded in real-time.\n\n"
            f"{config.EMOJIS['bullet']} **Log Feed Channel**: {channel.mention}\n"
            f"{config.EMOJIS['bullet']} **Monitored Activity**: Message edits, deletions, role shifts, voice transitions.\n"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
