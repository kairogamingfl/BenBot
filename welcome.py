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
