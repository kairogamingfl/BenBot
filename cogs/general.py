"""
BEN Discord Bot - General & Information Module
Interactive /help directory with category dropdowns, latency analytics, and server/user telemetry.
"""
import time
import platform
import psutil
import discord
from discord import app_commands, ui
from discord.ext import commands
from typing import Optional
from utils.embeds import BenEmbed, success_embed, info_embed
import config

class HelpCategorySelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="System Overview",
                value="overview",
                description="General bot overview, statistics & architecture",
                emoji="⚙️"
            ),
            discord.SelectOption(
                label="Welcome & Leave",
                value="welcome",
                description="Custom arrivals, farewells, and templates",
                emoji="👋"
            ),
            discord.SelectOption(
                label="Audit & Security Logs",
                value="logs",
                description="Real-time message, member & voice event logger",
                emoji="📜"
            ),
            discord.SelectOption(
                label="Broadcast Announcements",
                value="announcement",
                description="Modal-driven rich broadcast cards",
                emoji="📢"
            ),
            discord.SelectOption(
                label="Tickets & Support",
                value="tickets",
                description="Persistent panels, private rooms & transcripts",
                emoji="🎫"
            ),
            discord.SelectOption(
                label="Staff Applications",
                value="application",
                description="Screening questionnaires with Accept/Deny review",
                emoji="📝"
            ),
            discord.SelectOption(
                label="Component Reaction Roles",
                value="roles",
                description="Buttons & select menus for self-assigned roles",
                emoji="🎭"
            ),
            discord.SelectOption(
                label="Music & Audio Player",
                value="music",
                description="Voice stream controller, queue, and playback buttons",
                emoji="🎵"
            ),
            discord.SelectOption(
                label="Interactive Games",
                value="games",
                description="Tic-Tac-Toe, Rock-Paper-Scissors, Slots, Trivia",
                emoji="🎮"
            )
        ]
        super().__init__(
            placeholder="Explore commands by module category...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]

        if category == "overview":
            embed = BenEmbed(
                title=f"⚡  {config.BOT_NAME} SYSTEM • ARCHITECTURE OVERVIEW",
                description=(
                    f"### Professional Discord Management Suite ✦\n"
                    f"> **{config.BOT_NAME}** is built from the ground up for high-capacity communities.\n"
                    f"> Featuring seamless transparent embeds (`#2B2D31`), persistent UI buttons, and asynchronous SQLite storage.\n\n"
                    f"{config.EMOJIS['bullet']} **Command Architecture**: 100% Modern Discord Slash Commands (`/`)\n"
                    f"{config.EMOJIS['bullet']} **UI Components**: Interactive Buttons, Select Menus, & Input Modals\n"
                    f"{config.EMOJIS['bullet']} **Bot Version**: `{config.BOT_VERSION}`\n"
                    f"{config.EMOJIS['bullet']} **Latency**: `{round(interaction.client.latency * 1000)}ms`\n\n"
                    f"*Select a category from the dropdown below to inspect specific slash commands.*"
                )
            )
        elif category == "welcome":
            embed = BenEmbed(
                title="👋  WELCOME & FAREWELL COMMANDS",
                description=(
                    f"`/welcome setup <channel> [message]`\n> Configure the arrival greeting channel with custom tags.\n\n"
                    f"`/welcome test`\n> Dispatch a live preview of your welcome card to test layout.\n\n"
                    f"`/welcome toggle <enabled>`\n> Enable or disable arrival announcements.\n\n"
                    f"`/leave setup <channel> [message]`\n> Configure the member departure notices channel.\n\n"
                    f"`/leave test`\n> Dispatch a live preview of the departure card.\n\n"
                    f"**Available Template Variables**:\n"
                    f"`{{user}}` (Username), `{{mention}}` (@User), `{{server}}` (Guild Name), `{{member_count}}` (Total Members)"
                )
            )
        elif category == "logs":
            embed = BenEmbed(
                title="📜  AUDIT LOGGING COMMANDS",
                description=(
                    f"`/logs setup <channel>`\n> Designate the audit logging channel for all server events.\n\n"
                    f"`/logs toggle <enabled>`\n> Enable or pause real-time logging.\n\n"
                    f"**Monitored Audit Events**:\n"
                    f"{config.EMOJIS['bullet']} Message Purges & Deletions (with content & attachments)\n"
                    f"{config.EMOJIS['bullet']} Message Edits (before vs after diff)\n"
                    f"{config.EMOJIS['bullet']} Role Additions & Revocations\n"
                    f"{config.EMOJIS['bullet']} Nickname Modifications\n"
                    f"{config.EMOJIS['bullet']} Voice Channel Joins, Leaves & Movement\n"
                )
            )
        elif category == "announcement":
            embed = BenEmbed(
                title="📢  BROADCAST ANNOUNCEMENT COMMANDS",
                description=(
                    f"`/announce <channel> [mention] [theme]`\n"
                    f"> Opens an interactive Discord modal form to compose and dispatch a rich broadcast embed.\n\n"
                    f"{config.EMOJIS['bullet']} **Modal Inputs**: Title, Content (Markdown), Banner URL, Footer\n"
                    f"{config.EMOJIS['bullet']} **Pings**: `@everyone`, `@here`, or `none`\n"
                    f"{config.EMOJIS['bullet']} **Themes**: `transparent`, `primary`, `gold`, `mint`, `crimson`"
                )
            )
        elif category == "tickets":
            embed = BenEmbed(
                title="🎫  TICKET SUPPORT COMMANDS",
                description=(
                    f"`/ticket panel <channel> [category] [support_role] [title] [desc]`\n"
                    f"> Deploys a persistent **[ Create Ticket ]** button panel.\n\n"
                    f"`/ticket log_channel <channel>`\n"
                    f"> Sets the channel where closed ticket transcript files are archived.\n\n"
                    f"**Ticket Features**:\n"
                    f"{config.EMOJIS['bullet']} Automatic private channel creation with custom permissions\n"
                    f"{config.EMOJIS['bullet']} One-click Claim system for staff assignment\n"
                    f"{config.EMOJIS['bullet']} Instant transcript export with chat timestamps\n"
                    f"{config.EMOJIS['bullet']} Confirmation safety lock before deletion"
                )
            )
        elif category == "application":
            embed = BenEmbed(
                title="📝  STAFF APPLICATION COMMANDS",
                description=(
                    f"`/application panel <channel> <review_channel> [award_role] [title]`\n"
                    f"> Deploys an interactive **[ Submit Application ]** recruitment panel.\n\n"
                    f"**Recruitment Pipeline**:\n"
                    f"{config.EMOJIS['bullet']} 5-Question Modal questionnaire pops up on click\n"
                    f"{config.EMOJIS['bullet']} Submissions route to the staff review channel\n"
                    f"{config.EMOJIS['bullet']} Admins can click **[ Accept ]** or **[ Deny ]** directly\n"
                    f"{config.EMOJIS['bullet']} Automatic role granting upon acceptance + direct DM notification"
                )
            )
        elif category == "roles":
            embed = BenEmbed(
                title="🎭  REACTION & COMPONENT ROLES",
                description=(
                    f"`/reactionrole button_panel <channel> <title> <role1> [role2]...`\n"
                    f"> Creates a sleek button role board (supports up to 5 roles per row).\n\n"
                    f"`/reactionrole select_panel <channel> <title> <role1> [role2]...`\n"
                    f"> Creates a multi-select dropdown menu for toggling roles in bulk.\n\n"
                    f"{config.EMOJIS['bullet']} Instant role toggling without lag or emoji rate limits\n"
                    f"{config.EMOJIS['bullet']} Ephemeral status confirmation messages"
                )
            )
        elif category == "music":
            embed = BenEmbed(
                title="🎵  AUDIO STREAMING COMMANDS",
                description=(
                    f"`/music play <query>`\n> Stream audio from YouTube, Spotify, or audio URLs.\n\n"
                    f"`/music skip`\n> Skip to the next track in the playlist.\n\n"
                    f"`/music stop`\n> Disconnect and wipe the current playlist.\n\n"
                    f"`/music queue`\n> View the upcoming queued songs.\n\n"
                    f"**Interactive Dashboard**:\n"
                    f"Every track includes a control panel with `[ ⏯️ Pause ]`, `[ ⏭️ Skip ]`, `[ ⏹️ Stop ]`, `[ 📋 Queue ]` buttons."
                )
            )
        elif category == "games":
            embed = BenEmbed(
                title="🎮  INTERACTIVE UI GAMES",
                description=(
                    f"`/tictactoe <opponent>`\n> 3x3 interactive button grid duel against another player.\n\n"
                    f"`/rps [opponent]`\n> Rock-Paper-Scissors against BEN AI or a friend.\n\n"
                    f"`/trivia`\n> 4-choice button trivia covering Tech, Gaming, Science, and History.\n\n"
                    f"`/slots [bet]`\n> High-roller animated slot machine with jackpots.\n\n"
                    f"`/coinflip`\n> Weighted fair 50/50 coin toss.\n\n"
                    f"`/dice [sides]`\n> Polyhedral die roller (d6, d20, d100)."
                )
            )

        await interaction.response.edit_message(embed=embed)


class HelpView(ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(HelpCategorySelect())


class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = time.time()

    @app_commands.command(name="help", description="Open the interactive BEN command directory")
    async def help_cmd(self, interaction: discord.Interaction):
        embed = BenEmbed(
            title=f"⚡  {config.BOT_NAME} COMMAND DIRECTORY",
            description=(
                f"### Welcome to the **{config.BOT_NAME}** Management Console ✦\n"
                f"> Built with high-spec transparent embeds, instant UI components, and complete automation.\n\n"
                f"{config.EMOJIS['bullet']} **Select a Category**: Use the menu below to browse features.\n"
                f"{config.EMOJIS['bullet']} **Prefix**: Slash Commands (`/`)\n"
                f"{config.EMOJIS['bullet']} **Support**: Contact server administration\n\n"
                f"```yaml\n"
                f"Modules Loaded: Welcome • Logs • Announcements • Tickets\n"
                f"                Applications • ReactRoles • Music • Games\n"
                f"```"
            ),
            color=config.COLOR_TRANSPARENT,
            footer_text=f"{config.BOT_NAME} Core v{config.BOT_VERSION}"
        )
        if self.bot.user.display_avatar:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        view = HelpView()
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="ping", description="Inspect the bot WebSocket and API response latencies")
    async def ping(self, interaction: discord.Interaction):
        start = time.perf_counter()
        await interaction.response.defer(ephemeral=True)
        end = time.perf_counter()

        api_latency = round((end - start) * 1000)
        ws_latency = round(self.bot.latency * 1000)

        embed = BenEmbed(
            title="⚡  NETWORK LATENCY & TELEMETRY",
            description=(
                f"```ini\n"
                f"[SYSTEM OPERATIONAL]\n"
                f"WebSocket Latency : {ws_latency}ms\n"
                f"API Round-Trip    : {api_latency}ms\n"
                f"Status            : OPTIMAL\n"
                f"```\n"
                f"{config.EMOJIS['bullet']} **Gateway Connection**: `Stable`\n"
                f"{config.EMOJIS['bullet']} **Database Connection**: `Operational (aiosqlite)`\n"
            ),
            color=config.COLOR_TRANSPARENT
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="botinfo", description="Examine bot hardware, runtime statistics, and build info")
    async def botinfo(self, interaction: discord.Interaction):
        uptime_seconds = int(time.time() - self.start_time)
        uptime_str = f"<t:{int(self.start_time)}:R>"

        # Memory usage
        process = psutil.Process()
        mem_info = process.memory_info()
        mem_mb = mem_info.rss / 1024 / 1024

        embed = BenEmbed(
            title=f"🤖  {config.BOT_NAME} SYSTEM METRICS",
            description=f"> {config.BOT_DESCRIPTION}\n",
            color=config.COLOR_TRANSPARENT,
            thumbnail=self.bot.user.display_avatar.url if self.bot.user else None
        )
        embed.add_field(name="◈ Core Statistics", value=f"• Guilds: `{len(self.bot.guilds)}`\n• Users: `{sum(g.member_count for g in self.bot.guilds)}`\n• Commands: `{len(self.bot.tree.get_commands())}`", inline=True)
        embed.add_field(name="◈ Runtime & Hardware", value=f"• RAM: `{mem_mb:.2f} MB`\n• Python: `v{platform.python_version()}`\n• discord.py: `v{discord.__version__}`", inline=True)
        embed.add_field(name="◈ Uptime", value=f"• Online: {uptime_str}\n• Architecture: `{platform.system()} {platform.machine()}`", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="Display in-depth analytics and statistics for this server")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = BenEmbed(
            title=f"🏰  {guild.name.upper()}",
            description=f"> {guild.description or 'No server description set.'}\n",
            color=config.COLOR_TRANSPARENT,
            thumbnail=guild.icon.url if guild.icon else None
        )
        embed.add_field(name="◈ General", value=f"• Owner: {guild.owner.mention if guild.owner else 'Unknown'}\n• Created: <t:{int(guild.created_at.timestamp())}:R>\n• ID: `{guild.id}`", inline=True)
        embed.add_field(name="◈ Population", value=f"• Total Members: `{guild.member_count}`\n• Roles: `{len(guild.roles)}`\n• Boost Level: `Tier {guild.premium_tier}` ({guild.premium_subscription_count} boosts)", inline=True)
        embed.add_field(name="◈ Channels", value=f"• Text: `{len(guild.text_channels)}`\n• Voice: `{len(guild.voice_channels)}`\n• Categories: `{len(guild.categories)}`", inline=True)

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
