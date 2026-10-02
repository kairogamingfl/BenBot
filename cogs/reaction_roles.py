"""
BEN Discord Bot - Interactive Component Roles (Modern Reaction Roles)
Uses sleek Discord UI Buttons and Multi-Select Menus with real-time role toggles and ephemeral feedback.
"""
import discord
from discord import app_commands, ui
from discord.ext import commands
from typing import Optional, List
from utils.embeds import BenEmbed, success_embed, error_embed, info_embed
import config

class RoleButton(ui.Button):
    def __init__(self, role: discord.Role, emoji: Optional[str] = None, style: discord.ButtonStyle = discord.ButtonStyle.secondary):
        super().__init__(
            label=role.name,
            emoji=emoji or "🏷️",
            style=style,
            custom_id=f"ben:role_btn:{role.id}"
        )
        self.role_id = role.id

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        role = guild.get_role(self.role_id)

        if not role:
            await interaction.response.send_message(
                embed=error_embed("Role Missing", "This role appears to have been deleted from the server."),
                ephemeral=True
            )
            return

        if not guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message(
                embed=error_embed("Permission Fault", "I lack the `Manage Roles` permission to modify member roles."),
                ephemeral=True
            )
            return

        if role >= guild.me.top_role:
            await interaction.response.send_message(
                embed=error_embed("Hierarchy Restriction", f"The role {role.mention} sits higher than my highest role."),
                ephemeral=True
            )
            return

        if role in member.roles:
            await member.remove_roles(role, reason="BEN Interactive Role Panel")
            await interaction.response.send_message(
                embed=info_embed("Role Revoked", f"Successfully removed the role {role.mention}."),
                ephemeral=True
            )
        else:
            await member.add_roles(role, reason="BEN Interactive Role Panel")
            await interaction.response.send_message(
                embed=success_embed("Role Granted", f"Successfully assigned the role {role.mention}."),
                ephemeral=True
            )


class RoleSelectMenu(ui.Select):
    def __init__(self, roles: List[discord.Role], placeholder: str = "Select one or more roles..."):
        options = [
            discord.SelectOption(
                label=role.name[:100],
                value=str(role.id),
                description=f"Click to toggle {role.name}"[:100],
                emoji="🏷️"
            )
            for role in roles[:25]
        ]
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=len(options),
            options=options,
            custom_id="ben:role_select_dynamic"
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user

        if not guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message(
                embed=error_embed("Permission Fault", "I lack `Manage Roles` permission."),
                ephemeral=True
            )
            return

        added, removed = [], []
        for role_id_str in self.values:
            role = guild.get_role(int(role_id_str))
            if not role or role >= guild.me.top_role:
                continue
            if role in member.roles:
                await member.remove_roles(role, reason="BEN Dropdown Role Menu")
                removed.append(role.name)
            else:
                await member.add_roles(role, reason="BEN Dropdown Role Menu")
                added.append(role.name)

        summary_parts = []
        if added:
            summary_parts.append(f"**Added**: " + ", ".join([f"`{r}`" for r in added]))
        if removed:
            summary_parts.append(f"**Removed**: " + ", ".join([f"`{r}`" for r in removed]))

        status_text = "\n".join(summary_parts) if summary_parts else "No modifications were executed."

        await interaction.response.send_message(
            embed=success_embed("Roles Synchronized", status_text),
            ephemeral=True
        )


class DynamicButtonRolesView(ui.View):
    """Dynamic persistent container for button roles."""
    def __init__(self):
        super().__init__(timeout=None)


class ReactionRoles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    roles_group = app_commands.Group(name="reactionrole", description="Build interactive button and menu role assigners")

    @roles_group.command(name="button_panel", description="Deploy a transparent button-based role picker")
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.describe(
        channel="Channel to deploy the button panel",
        title="Title of the panel",
        role1="Primary Role",
        role2="Secondary Role (Optional)",
        role3="Tertiary Role (Optional)",
        role4="Fourth Role (Optional)",
        role5="Fifth Role (Optional)"
    )
    async def create_button_panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        title: str,
        role1: discord.Role,
        role2: Optional[discord.Role] = None,
        role3: Optional[discord.Role] = None,
        role4: Optional[discord.Role] = None,
        role5: Optional[discord.Role] = None,
        description: Optional[str] = None
    ):
        roles = [r for r in [role1, role2, role3, role4, role5] if r is not None]

        view = DynamicButtonRolesView()
        role_bullet_list = []
        for role in roles:
            view.add_item(RoleButton(role))
            role_bullet_list.append(f"{config.EMOJIS['bullet']} {role.mention}")

        desc = description or (
            "### Self-Assignable Roles ✦\n"
            "> Click any of the interactive buttons below to toggle that role on or off.\n\n"
            + "\n".join(role_bullet_list)
        )

        embed = BenEmbed(
            title=f"🎭  {title.upper()}",
            description=desc,
            color=config.COLOR_TRANSPARENT,
            footer_text=f"{config.BOT_NAME} Role Infrastructure"
        )
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)

        msg = await channel.send(embed=embed, view=view)

        # Store in DB
        for role in roles:
            await self.bot.db.add_reaction_role(
                interaction.guild_id, channel.id, msg.id, role.id, "🏷️", role.name
            )

        await interaction.response.send_message(
            embed=success_embed("Role Panel Published", f"Button role menu generated in {channel.mention}."),
            ephemeral=True
        )

    @roles_group.command(name="select_panel", description="Deploy a clean dropdown menu for selecting roles")
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.describe(
        channel="Channel to deploy the dropdown menu",
        title="Title of the panel",
        role1="First Role",
        role2="Second Role (Optional)",
        role3="Third Role (Optional)",
        role4="Fourth Role (Optional)",
        role5="Fifth Role (Optional)"
    )
    async def create_select_panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        title: str,
        role1: discord.Role,
        role2: Optional[discord.Role] = None,
        role3: Optional[discord.Role] = None,
        role4: Optional[discord.Role] = None,
        role5: Optional[discord.Role] = None,
        placeholder: Optional[str] = None
    ):
        roles = [r for r in [role1, role2, role3, role4, role5] if r is not None]

        view = ui.View(timeout=None)
        select = RoleSelectMenu(roles, placeholder=placeholder or "Choose your roles from this list...")
        view.add_item(select)

        desc = (
            "### Role Directory ✦\n"
            "> Open the dropdown menu below and choose which roles you'd like to assign.\n"
            "> Re-selecting a role will toggle it off.\n\n"
            + "\n".join([f"{config.EMOJIS['bullet']} {r.mention}" for r in roles])
        )

        embed = BenEmbed(
            title=f"🎭  {title.upper()}",
            description=desc,
            color=config.COLOR_TRANSPARENT,
            footer_text=f"{config.BOT_NAME} Role Infrastructure"
        )
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)

        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(
            embed=success_embed("Dropdown Menu Published", f"Dropdown role panel deployed in {channel.mention}."),
            ephemeral=True
        )

    # Listen for button interactions with dynamic prefix
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get("custom_id", "")
        if custom_id.startswith("ben:role_btn:"):
            role_id = int(custom_id.split(":")[-1])
            guild = interaction.guild
            member = interaction.user
            role = guild.get_role(role_id)

            if not role:
                await interaction.response.send_message(embed=error_embed("Error", "Role no longer exists."), ephemeral=True)
                return

            if role in member.roles:
                await member.remove_roles(role, reason="BEN Role Toggle")
                await interaction.response.send_message(embed=info_embed("Role Removed", f"Removed {role.mention}."), ephemeral=True)
            else:
                await member.add_roles(role, reason="BEN Role Toggle")
                await interaction.response.send_message(embed=success_embed("Role Added", f"Granted {role.mention}."), ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ReactionRoles(bot))
