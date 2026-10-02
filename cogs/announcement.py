"""
BEN Discord Bot - Announcement System
Delivers high-visibility, modal-driven broadcast cards with transparent aesthetic and ping management.
"""
import discord
from discord import app_commands, ui
from discord.ext import commands
from typing import Optional, Literal
from utils.embeds import BenEmbed, success_embed, error_embed
import config

class AnnouncementModal(ui.Modal, title="Broadcast Announcement"):
    def __init__(self, target_channel: discord.TextChannel, mention_type: str, color_hex: int):
        super().__init__()
        self.target_channel = target_channel
        self.mention_type = mention_type
        self.color_hex = color_hex

    announcement_title = ui.TextInput(
        label="Announcement Title",
        placeholder="e.g. OFFICIAL SERVER NOTICE // UPDATE v2.5",
        max_length=100,
        required=True
    )

    announcement_content = ui.TextInput(
        label="Message Content (Supports Markdown)",
        style=discord.TextStyle.paragraph,
        placeholder="Enter the detailed announcement body here...\nUse markdown bullet points, bold text, etc.",
        max_length=3500,
        required=True
    )

    banner_url = ui.TextInput(
        label="Image / Banner URL (Optional)",
        placeholder="https://example.com/banner.png",
        max_length=300,
        required=False
    )

    footer_note = ui.TextInput(
        label="Custom Footer Note (Optional)",
        placeholder="e.g. Server Administration Team",
        max_length=80,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        embed = BenEmbed(
            title=f"📢  {self.announcement_title.value.upper()}",
            description=self.announcement_content.value,
            color=self.color_hex,
            author_name=interaction.guild.name,
            author_icon=interaction.guild.icon.url if interaction.guild.icon else None,
            footer_text=self.footer_note.value or f"Broadcasted by {interaction.user.display_name}"
        )

        if self.banner_url.value and self.banner_url.value.startswith(("http://", "https://")):
            embed.set_image(url=self.banner_url.value)

        # Handle mentions
        ping_text = None
        if self.mention_type == "everyone":
            ping_text = "@everyone"
        elif self.mention_type == "here":
            ping_text = "@here"

        try:
            await self.target_channel.send(content=ping_text, embed=embed)
            await interaction.response.send_message(
                embed=success_embed("Broadcast Dispatched", f"Announcement successfully delivered to {self.target_channel.mention}."),
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=error_embed("Permission Denied", f"I do not possess permissions to post in {self.target_channel.mention}."),
                ephemeral=True
            )


class Announcement(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="announce", description="Construct and publish a broadcast embed via an interactive modal")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(
        channel="The text channel where the announcement will be published",
        mention="Choose whether to ping everyone, here, or none",
        theme="Choose the embed style"
    )
    async def announce(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        mention: Literal["none", "everyone", "here"] = "none",
        theme: Literal["transparent", "primary", "gold", "mint", "crimson"] = "transparent"
    ):
        theme_colors = {
            "transparent": config.COLOR_TRANSPARENT,
            "primary": config.COLOR_PRIMARY,
            "gold": config.COLOR_WARNING,
            "mint": config.COLOR_SUCCESS,
            "crimson": config.COLOR_ERROR
        }
        chosen_color = theme_colors.get(theme, config.COLOR_TRANSPARENT)
        modal = AnnouncementModal(target_channel=channel, mention_type=mention, color_hex=chosen_color)
        await interaction.response.send_modal(modal)

async def setup(bot: commands.Bot):
    await bot.add_cog(Announcement(bot))
