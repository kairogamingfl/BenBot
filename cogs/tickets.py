"""
BEN Discord Bot - Enterprise Ticket Support System
Persistent buttons, private channel orchestration, transcript generation, and claim dispatch.
"""
import io
import asyncio
import discord
from discord import app_commands, ui
from discord.ext import commands
from typing import Optional
from utils.embeds import BenEmbed, success_embed, error_embed, info_embed
import config

class TicketControlView(ui.View):
    """Controls inside an active ticket channel: Close, Claim, Transcript."""
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ben:ticket_close")
    async def close_ticket(self, interaction: discord.Interaction, button: ui.Button):
        confirm_view = TicketConfirmCloseView(self.bot, interaction.channel)
        await interaction.response.send_message(
            content="⚠️ **Are you sure you want to close and archive this ticket?**",
            view=confirm_view,
            ephemeral=True
        )

    @ui.button(label="Claim Ticket", style=discord.ButtonStyle.success, emoji="🙋", custom_id="ben:ticket_claim")
    async def claim_ticket(self, interaction: discord.Interaction, button: ui.Button):
        # Update permissions or announce
        embed = BenEmbed(
            title="🙋  TICKET CLAIMED",
            description=f"This support session has been claimed by {interaction.user.mention}.\nThey will be assisting you from here on.",
            color=config.COLOR_SUCCESS
        )
        button.disabled = True
        button.label = f"Claimed by {interaction.user.name}"
        await interaction.response.edit_message(view=self)
        await interaction.channel.send(embed=embed)

    @ui.button(label="Save Transcript", style=discord.ButtonStyle.secondary, emoji="📋", custom_id="ben:ticket_transcript")
    async def transcript_ticket(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)
        file = await generate_transcript_file(interaction.channel)
        await interaction.followup.send(
            content="📄 **Here is your live ticket transcript:**",
            file=file,
            ephemeral=True
        )


class TicketConfirmCloseView(ui.View):
    def __init__(self, bot: commands.Bot, channel: discord.TextChannel):
        super().__init__(timeout=60)
        self.bot = bot
        self.channel = channel

    @ui.button(label="Confirm & Delete Channel", style=discord.ButtonStyle.danger, emoji="✅")
    async def confirm_close(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("🔒 **Archiving ticket and preparing transcript... Channel will close in 5 seconds.**")
        
        # Mark in database
        await self.bot.db.close_ticket(self.channel.id, interaction.user.id)
        
        # Generate transcript
        transcript_file = await generate_transcript_file(self.channel)
        
        # Check for ticket log channel
        settings = await self.bot.db.get_guild_settings(interaction.guild_id)
        log_channel_id = settings.get("ticket_log_channel_id")
        if log_channel_id:
            log_chan = interaction.guild.get_channel(log_channel_id)
            if log_chan:
                log_embed = BenEmbed(
                    title="📁  TICKET ARCHIVED",
                    color=config.COLOR_TRANSPARENT,
                    footer_text=f"Closed by {interaction.user}"
                )
                log_embed.description = (
                    f"{config.EMOJIS['bullet']} **Ticket**: `{self.channel.name}`\n"
                    f"{config.EMOJIS['bullet']} **Closed By**: {interaction.user.mention} (`{interaction.user.id}`)\n"
                )
                try:
                    await log_chan.send(embed=log_embed, file=transcript_file)
                except Exception:
                    pass

        await asyncio.sleep(5)
        try:
            await self.channel.delete(reason=f"Ticket closed by {interaction.user}")
        except Exception:
            pass

    @ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_close(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("Closure cancelled.", ephemeral=True)
        self.stop()


class TicketLauncherView(ui.View):
    """The persistent button on the main Ticket Panel."""
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @ui.button(label="Create Ticket", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="ben:open_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: ui.Button):
        guild = interaction.guild
        member = interaction.user

        await interaction.response.defer(ephemeral=True)

        settings = await self.bot.db.get_guild_settings(guild.id)
        category_id = settings.get("ticket_category_id")
        support_role_id = settings.get("ticket_support_role_id")

        category = guild.get_channel(category_id) if category_id else None
        support_role = guild.get_role(support_role_id) if support_role_id else None

        ticket_num = await self.bot.db.increment_ticket_counter(guild.id)
        channel_name = f"ticket-{ticket_num:04d}"

        # Setup Overwrites
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True)

        try:
            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                reason=f"Support ticket opened by {member}"
            )
        except discord.Forbidden:
            await interaction.followup.send(
                embed=error_embed("Permission Error", "I lack the `Manage Channels` permission to create ticket rooms."),
                ephemeral=True
            )
            return

        # Store in database
        await self.bot.db.create_ticket(guild.id, ticket_channel.id, member.id, ticket_num)

        # Welcome message inside the ticket channel
        welcome_embed = BenEmbed(
            title=f"🎫  TICKET #{ticket_num:04d} • SUPPORT DESK",
            description=(
                f"Welcome {member.mention}! Thank you for getting in touch.\n\n"
                f"> **Instructions**: Please state your query, issue, or request with relevant details.\n"
                f"> Our support team has been notified and will be with you promptly.\n\n"
                f"{config.EMOJIS['bullet']} **Creator**: {member.mention} (`{member.id}`)\n"
                f"{config.EMOJIS['bullet']} **Created At**: <t:{int(discord.utils.utcnow().timestamp())}:F>\n"
            ),
            color=config.COLOR_TRANSPARENT,
            thumbnail=member.display_avatar.url
        )
        
        control_view = TicketControlView(self.bot)
        role_mention = support_role.mention if support_role else ""
        await ticket_channel.send(content=f"{member.mention} {role_mention}", embed=welcome_embed, view=control_view)

        await interaction.followup.send(
            embed=success_embed("Ticket Created", f"Your private support channel is ready at {ticket_channel.mention}."),
            ephemeral=True
        )


async def generate_transcript_file(channel: discord.TextChannel) -> discord.File:
    """Creates a clean human-readable text transcript of a channel."""
    lines = [
        f"============================================================",
        f"BEN SYSTEM - TICKET AUDIT LOG",
        f"Channel: #{channel.name} ({channel.id})",
        f"Server:  {channel.guild.name} ({channel.guild.id})",
        f"Exported: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"============================================================\n"
    ]

    async for msg in channel.history(limit=500, oldest_first=True):
        timestamp = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
        author = f"{msg.author.name}#{msg.author.discriminator if hasattr(msg.author, 'discriminator') and msg.author.discriminator != '0' else ''}"
        clean_content = msg.clean_content or "[No Text]"
        lines.append(f"[{timestamp}] {author}: {clean_content}")
        for att in msg.attachments:
            lines.append(f"    [Attachment: {att.filename} -> {att.url}]")

    content = "\n".join(lines)
    buffer = io.BytesIO(content.encode("utf-8"))
    return discord.File(fp=buffer, filename=f"transcript-{channel.name}.txt")


class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Register persistent view so buttons work across restarts
        self.bot.add_view(TicketLauncherView(bot))
        self.bot.add_view(TicketControlView(bot))

    ticket_group = app_commands.Group(name="ticket", description="Manage ticket support infrastructure")

    @ticket_group.command(name="panel", description="Deploy the interactive Ticket Creation Panel")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        channel="Channel to deploy the panel in",
        category="Target category where new ticket channels will be generated",
        support_role="Staff role allowed to view and manage tickets",
        title="Custom panel title",
        description="Custom panel description"
    )
    async def ticket_panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        category: Optional[discord.CategoryChannel] = None,
        support_role: Optional[discord.Role] = None,
        title: Optional[str] = None,
        description: Optional[str] = None
    ):
        if category:
            await self.bot.db.update_guild_setting(interaction.guild_id, "ticket_category_id", category.id)
        if support_role:
            await self.bot.db.update_guild_setting(interaction.guild_id, "ticket_support_role_id", support_role.id)

        panel_title = title or "SUPPORT DESK & TICKETS"
        panel_desc = description or (
            "### Need Assistance or Have Inquiries? ✦\n"
            "> Click the button below to generate a private ticket channel.\n"
            "> Our dedicated staff team is here to assist with billing, questions, or player reports.\n\n"
            f"{config.EMOJIS['bullet']} **Response Time**: Usually under a few minutes\n"
            f"{config.EMOJIS['bullet']} **Privacy**: Only you and qualified staff have access\n"
        )

        embed = BenEmbed(
            title=f"🎫  {panel_title.upper()}",
            description=panel_desc,
            color=config.COLOR_TRANSPARENT,
            footer_text=f"{config.BOT_NAME} Support Core • Click below to start"
        )
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)

        view = TicketLauncherView(self.bot)
        await channel.send(embed=embed, view=view)

        await interaction.response.send_message(
            embed=success_embed("Panel Published", f"Ticket launch pad successfully placed in {channel.mention}."),
            ephemeral=True
        )

    @ticket_group.command(name="log_channel", description="Set the destination channel for ticket closure transcripts")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_log_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.bot.db.update_guild_setting(interaction.guild_id, "ticket_log_channel_id", channel.id)
        await interaction.response.send_message(
            embed=success_embed("Log Channel Bound", f"Closed ticket transcripts will now be forwarded to {channel.mention}."),
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
