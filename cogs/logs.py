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

    @logs_group.command(name="toggle", description="Turn audit logging on or off")
    @app_commands.checks.has_permissions(administrator=True)
    async def logs_toggle(self, interaction: discord.Interaction, enabled: bool):
        await self.db.update_guild_setting(interaction.guild_id, "log_enabled", 1 if enabled else 0)
        status = "enabled" if enabled else "disabled"
        await interaction.response.send_message(
            embed=success_embed("System Updated", f"Audit logging is now **{status}**."),
            ephemeral=True
        )

    # --- Message Events ---
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        log_channel = await self.get_log_channel(message.guild)
        if not log_channel:
            return

        embed = BenEmbed(
            title="🗑️  MESSAGE PURGED / DELETED",
            color=config.COLOR_ERROR,
            thumbnail=message.author.display_avatar.url,
            footer_text=f"Author ID: {message.author.id} • Channel ID: {message.channel.id}"
        )
        embed.description = (
            f"{config.EMOJIS['bullet']} **Author**: {message.author.mention} (`{message.author}`)\n"
            f"{config.EMOJIS['bullet']} **Channel**: {message.channel.mention}\n\n"
            f"**Deleted Content:**\n"
            f"```{message.clean_content[:1800] if message.clean_content else '[No text / Media attachment]'}```"
        )
        if message.attachments:
            files_desc = "\n".join([f"• [{att.filename}]({att.url})" for att in message.attachments])
            embed.add_field(name="Attached Files", value=files_desc[:1024], inline=False)

        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or not before.guild or before.content == after.content:
            return
        log_channel = await self.get_log_channel(before.guild)
        if not log_channel:
            return

        embed = BenEmbed(
            title="✏️  MESSAGE MODIFIED",
            color=config.COLOR_WARNING,
            thumbnail=before.author.display_avatar.url,
            footer_text=f"Author ID: {before.author.id} • Message ID: {before.id}"
        )
        embed.description = (
            f"{config.EMOJIS['bullet']} **Author**: {before.author.mention} (`{before.author}`)\n"
            f"{config.EMOJIS['bullet']} **Channel**: {before.channel.mention} • [Jump to Message]({after.jump_url})\n\n"
            f"**Before:**\n```{before.clean_content[:800] or '[Empty]'}```\n"
            f"**After:**\n```{after.clean_content[:800] or '[Empty]'}```"
        )
        await log_channel.send(embed=embed)

    # --- Member & Role Events ---
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        log_channel = await self.get_log_channel(before.guild)
        if not log_channel:
            return

        # Check for role additions/removals
        if before.roles != after.roles:
            added = [r for r in after.roles if r not in before.roles]
            removed = [r for r in before.roles if r not in after.roles]

            if added or removed:
                embed = BenEmbed(
                    title="🛡️  MEMBER ROLES UPDATED",
                    color=config.COLOR_PRIMARY,
                    thumbnail=after.display_avatar.url,
                    footer_text=f"User ID: {after.id}"
                )
                desc = f"{config.EMOJIS['bullet']} **Target**: {after.mention} (`{after}`)\n\n"
                if added:
                    desc += f"**Roles Granted:**\n" + " ".join([r.mention for r in added]) + "\n"
                if removed:
                    desc += f"**Roles Revoked:**\n" + " ".join([r.mention for r in removed]) + "\n"
                embed.description = desc
                await log_channel.send(embed=embed)

        # Check for nickname changes
        if before.nick != after.nick:
            embed = BenEmbed(
                title="🏷️  NICKNAME CHANGED",
                color=config.COLOR_TRANSPARENT,
                thumbnail=after.display_avatar.url,
                footer_text=f"User ID: {after.id}"
            )
            embed.description = (
                f"{config.EMOJIS['bullet']} **Member**: {after.mention}\n"
                f"{config.EMOJIS['bullet']} **Old Nickname**: `{before.nick or before.name}`\n"
                f"{config.EMOJIS['bullet']} **New Nickname**: `{after.nick or after.name}`\n"
            )
            await log_channel.send(embed=embed)

    # --- Voice Movements ---
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if before.channel == after.channel:
            return
        log_channel = await self.get_log_channel(member.guild)
        if not log_channel:
            return

        embed = BenEmbed(
            title="🎙️  VOICE ACTIVITY",
            color=config.COLOR_TRANSPARENT,
            thumbnail=member.display_avatar.url,
            footer_text=f"User ID: {member.id}"
        )
        if not before.channel and after.channel:
            embed.description = f"{config.EMOJIS['bullet']} **Action**: Connected to voice\n{config.EMOJIS['bullet']} **Member**: {member.mention}\n{config.EMOJIS['bullet']} **Channel**: `{after.channel.name}`"
        elif before.channel and not after.channel:
            embed.description = f"{config.EMOJIS['bullet']} **Action**: Disconnected from voice\n{config.EMOJIS['bullet']} **Member**: {member.mention}\n{config.EMOJIS['bullet']} **Channel**: `{before.channel.name}`"
        elif before.channel and after.channel:
            embed.description = f"{config.EMOJIS['bullet']} **Action**: Switched voice channel\n{config.EMOJIS['bullet']} **Member**: {member.mention}\n{config.EMOJIS['bullet']} **From**: `{before.channel.name}` ➔ **To**: `{after.channel.name}`"

        await log_channel.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Logs(bot))
