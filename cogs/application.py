"""
BEN Discord Bot - Staff & Member Application Framework
Modal screening questionnaires, admin review workflows with inline Accept/Deny dispatch and DM notifications.
"""
import json
import discord
from discord import app_commands, ui
from discord.ext import commands
from typing import Optional
from utils.embeds import BenEmbed, success_embed, error_embed, info_embed
import config

class StaffApplicationModal(ui.Modal, title="Staff Recruitment Application"):
    def __init__(self, bot: commands.Bot, review_channel_id: int, role_id: Optional[int]):
        super().__init__()
        self.bot = bot
        self.review_channel_id = review_channel_id
        self.role_id = role_id

    age_timezone = ui.TextInput(
        label="1. Age & Timezone",
        placeholder="e.g. 19 | UTC-5 (EST)",
        max_length=60,
        required=True
    )

    desired_role = ui.TextInput(
        label="2. Desired Position",
        placeholder="e.g. Moderator / Event Host / Helper / Admin",
        max_length=60,
        required=True
    )

    experience = ui.TextInput(
        label="3. Prior Moderation Experience",
        style=discord.TextStyle.paragraph,
        placeholder="List any servers you have previously staffed or moderated, and your responsibilities...",
        max_length=1000,
        required=True
    )

    motivation = ui.TextInput(
        label="4. Why should we choose you?",
        style=discord.TextStyle.paragraph,
        placeholder="What unique strengths, traits, or activity levels do you bring to the server?",
        max_length=1000,
        required=True
    )

    scenario = ui.TextInput(
        label="5. Scenario: Severe Raid or Toxic Member",
        style=discord.TextStyle.paragraph,
        placeholder="How do you defuse tension and apply server protocol during chaos?",
        max_length=1000,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        answers = {
            "Age & Timezone": self.age_timezone.value,
            "Position": self.desired_role.value,
            "Experience": self.experience.value,
            "Motivation": self.motivation.value,
            "Scenario Resolution": self.scenario.value,
        }

        # Store in database
        app_id = await self.bot.db.create_application(
            interaction.guild_id, interaction.user.id, json.dumps(answers)
        )

        review_chan = interaction.guild.get_channel(self.review_channel_id)
        if not review_chan:
            await interaction.response.send_message(
                embed=error_embed("Config Error", "The review channel is no longer accessible. Please notify administrators."),
                ephemeral=True
            )
            return

        # Build Review Embed
        review_embed = BenEmbed(
            title=f"📋  NEW APPLICATION #{app_id:04d}",
            color=config.COLOR_TRANSPARENT,
            thumbnail=interaction.user.display_avatar.url,
            footer_text=f"Applicant ID: {interaction.user.id} • Status: PENDING REVIEW"
        )
        review_embed.description = (
            f"{config.EMOJIS['bullet']} **Applicant**: {interaction.user.mention} (`{interaction.user}`)\n"
            f"{config.EMOJIS['bullet']} **Account Created**: <t:{int(interaction.user.created_at.timestamp())}:R>\n"
            f"{config.EMOJIS['bullet']} **Joined Server**: <t:{int(interaction.user.joined_at.timestamp()) if interaction.user.joined_at else 0}:R>\n"
            f"──────────────────────────────\n"
        )

        for q, a in answers.items():
            review_embed.add_field(name=f"◈ {q}", value=f"```{a}```", inline=False)

        review_view = ApplicationDecisionView(self.bot, app_id, interaction.user.id, self.role_id)
        await review_chan.send(embed=review_embed, view=review_view)

        await interaction.response.send_message(
            embed=success_embed(
                "Application Submitted",
                "Your application has been received by senior management. You will be notified via Direct Message once reviewed."
            ),
            ephemeral=True
        )


class ReasonDecisionModal(ui.Modal):
    def __init__(self, action: str, on_confirm_callback):
        super().__init__(title=f"Reason for {action.capitalize()}")
        self.action = action
        self.on_confirm_callback = on_confirm_callback

    reason_input = ui.TextInput(
        label="Reviewer Notes / Feedback to Applicant",
        style=discord.TextStyle.paragraph,
        placeholder="Enter constructive remarks or official reasoning...",
        max_length=500,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await self.on_confirm_callback(interaction, self.reason_input.value or "No additional remarks.")


class ApplicationDecisionView(ui.View):
    """Buttons inside the review channel for Admins to Accept or Deny."""
    def __init__(self, bot: commands.Bot, app_id: int, applicant_id: int, role_id: Optional[int]):
        super().__init__(timeout=None)
        self.bot = bot
        self.app_id = app_id
        self.applicant_id = applicant_id
        self.role_id = role_id

    @ui.button(label="Accept Application", style=discord.ButtonStyle.success, emoji="✅")
    async def accept_button(self, interaction: discord.Interaction, button: ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(embed=error_embed("Denied", "Only Administrators can review applications."), ephemeral=True)
            return

        async def execute_accept(modal_interaction: discord.Interaction, notes: str):
            await self.bot.db.update_application_status(self.app_id, "accepted", modal_interaction.user.id, notes)
            
            # Give role if configured
            guild = modal_interaction.guild
            member = guild.get_member(self.applicant_id)
            role_awarded = False
            if member and self.role_id:
                role = guild.get_role(self.role_id)
                if role and guild.me.guild_permissions.manage_roles:
                    try:
                        await member.add_roles(role, reason=f"Application #{self.app_id} Approved")
                        role_awarded = True
                    except Exception:
                        pass

            # DM applicant
            if member:
                try:
                    role_line = f"{config.EMOJIS['bullet']} **Role Granted**: <@&{self.role_id}>\n" if role_awarded else ""
                    dm_desc = (
                        f"Congratulations! Your application for **{guild.name}** has been **APPROVED**.\n\n"
                        f"{config.EMOJIS['bullet']} **Reviewer**: {modal_interaction.user.mention}\n"
                        f"{config.EMOJIS['bullet']} **Notes**: {notes}\n"
                        f"{role_line}"
                    )
                    dm_embed = BenEmbed(
                        title=f"{config.EMOJIS['check']}  APPLICATION ACCEPTED",
                        description=dm_desc,
                        color=config.COLOR_SUCCESS
                    )
                    await member.send(embed=dm_embed)
                except Exception:
                    pass

            # Update original message
            orig_embed = modal_interaction.message.embeds[0]
            new_embed = BenEmbed(
                title=f"📋  APPLICATION #{self.app_id:04d} • [ACCEPTED]",
                color=config.COLOR_SUCCESS,
                thumbnail=orig_embed.thumbnail.url if orig_embed.thumbnail else None,
                footer_text=f"Approved by {modal_interaction.user} • Today"
            )
            new_embed.description = (
                f"{config.EMOJIS['bullet']} **Applicant**: <@{self.applicant_id}>\n"
                f"{config.EMOJIS['bullet']} **Decision**: **ACCEPTED** by {modal_interaction.user.mention}\n"
                f"{config.EMOJIS['bullet']} **Staff Feedback**: `{notes}`\n"
            )
            for f in orig_embed.fields:
                new_embed.add_field(name=f.name, value=f.value, inline=False)

            # Disable all buttons
            for child in self.children:
                child.disabled = True

            await modal_interaction.response.edit_message(embed=new_embed, view=self)

        modal = ReasonDecisionModal(action="Approval", on_confirm_callback=execute_accept)
        await interaction.response.send_modal(modal)

    @ui.button(label="Deny Application", style=discord.ButtonStyle.danger, emoji="❌")
    async def deny_button(self, interaction: discord.Interaction, button: ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(embed=error_embed("Denied", "Only Administrators can review applications."), ephemeral=True)
            return

        async def execute_deny(modal_interaction: discord.Interaction, notes: str):
            await self.bot.db.update_application_status(self.app_id, "denied", modal_interaction.user.id, notes)
            guild = modal_interaction.guild
            member = guild.get_member(self.applicant_id)

            # DM applicant
            if member:
                try:
                    dm_embed = BenEmbed(
                        title=f"{config.EMOJIS['cross']}  APPLICATION STATUS UPDATE",
                        description=(
                            f"Thank you for your interest in **{guild.name}**.\n"
                            f"After careful deliberation, your application was **NOT ACCEPTED** at this time.\n\n"
                            f"{config.EMOJIS['bullet']} **Feedback**: {notes}\n\n"
                            f"> Feel free to re-apply in the future."
                        ),
                        color=config.COLOR_ERROR
                    )
                    await member.send(embed=dm_embed)
                except Exception:
                    pass

            # Update original review message
            orig_embed = modal_interaction.message.embeds[0]
            new_embed = BenEmbed(
                title=f"📋  APPLICATION #{self.app_id:04d} • [DENIED]",
                color=config.COLOR_ERROR,
                thumbnail=orig_embed.thumbnail.url if orig_embed.thumbnail else None,
                footer_text=f"Denied by {modal_interaction.user} • Today"
            )
            new_embed.description = (
                f"{config.EMOJIS['bullet']} **Applicant**: <@{self.applicant_id}>\n"
                f"{config.EMOJIS['bullet']} **Decision**: **DENIED** by {modal_interaction.user.mention}\n"
                f"{config.EMOJIS['bullet']} **Staff Feedback**: `{notes}`\n"
            )
            for f in orig_embed.fields:
                new_embed.add_field(name=f.name, value=f.value, inline=False)

            for child in self.children:
                child.disabled = True

            await modal_interaction.response.edit_message(embed=new_embed, view=self)

        modal = ReasonDecisionModal(action="Denial", on_confirm_callback=execute_deny)
        await interaction.response.send_modal(modal)


class ApplicationLauncherView(ui.View):
    """The persistent Apply button placed on the public Application Panel."""
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @ui.button(label="Submit Application", style=discord.ButtonStyle.primary, emoji="📝", custom_id="ben:apply_now")
    async def apply_button(self, interaction: discord.Interaction, button: ui.Button):
        settings = await self.bot.db.get_guild_settings(interaction.guild_id)
        review_channel_id = settings.get("app_review_channel_id")
        role_id = settings.get("app_role_id")

        if not review_channel_id:
            await interaction.response.send_message(
                embed=error_embed("Setup Incomplete", "The administration has not designated an application review channel yet."),
                ephemeral=True
            )
            return

        modal = StaffApplicationModal(self.bot, review_channel_id, role_id)
        await interaction.response.send_modal(modal)


class Applications(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(ApplicationLauncherView(bot))

    app_group = app_commands.Group(name="application", description="Configure recruitment applications")

    @app_group.command(name="panel", description="Deploy the persistent Staff Application Panel")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        channel="Channel to deploy the public application panel",
        review_channel="Restricted staff channel where incoming applications will be vetted",
        award_role="Role to grant automatically if the application is accepted",
        title="Custom panel title",
        description="Custom description text"
    )
    async def application_panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        review_channel: discord.TextChannel,
        award_role: Optional[discord.Role] = None,
        title: Optional[str] = None,
        description: Optional[str] = None
    ):
        await self.bot.db.update_guild_setting(interaction.guild_id, "app_channel_id", channel.id)
        await self.bot.db.update_guild_setting(interaction.guild_id, "app_review_channel_id", review_channel.id)
        if award_role:
            await self.bot.db.update_guild_setting(interaction.guild_id, "app_role_id", award_role.id)

        panel_title = title or "STAFF & MODERATOR RECRUITMENT"
        panel_desc = description or (
            "### Join Our Community Administration Team ✦\n"
            "> Are you motivated, responsible, and looking to assist in cultivating a secure, vibrant community?\n"
            "> We are actively reviewing prospective candidates for our staff division.\n\n"
            f"{config.EMOJIS['bullet']} **Requirements**: Active member, maturity, conflict resolution abilities\n"
            f"{config.EMOJIS['bullet']} **Review Flow**: Fast-track review directly by Senior Management\n\n"
            "*Click the button below to complete the secure questionnaire.*"
        )

        embed = BenEmbed(
            title=f"📝  {panel_title.upper()}",
            description=panel_desc,
            color=config.COLOR_TRANSPARENT,
            footer_text=f"{config.BOT_NAME} Recruitment Engine • Click below to apply"
        )
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)

        view = ApplicationLauncherView(self.bot)
        await channel.send(embed=embed, view=view)

        await interaction.response.send_message(
            embed=success_embed(
                "Recruitment Panel Deployed",
                f"Application panel launched in {channel.mention}.\nSubmissions routed to {review_channel.mention}."
            ),
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Applications(bot))
