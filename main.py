"""
=============================================================================
                      BEN DISCORD BOT - CORE RUNTIME
               Engineered with Transparent Dark Theme Aesthetic
=============================================================================
"""
import os
import sys
import asyncio
import itertools
import discord
from discord import app_commands
from discord.ext import commands, tasks
from colorama import Fore, Style, init

import config
from utils.database import Database
from utils.embeds import error_embed, BenEmbed

init(autoreset=True)

class BenBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix=commands.when_mentioned_or(config.BOT_PREFIX),
            intents=intents,
            help_command=None,
            application_id=config.APPLICATION_ID
        )
        self.db = Database()
        self.status_cycle = None

    async def setup_hook(self):
        """Pre-login lifecycle hook: loads database, extensions, and registers persistent UI views."""
        print(f"{Fore.CYAN}──────────────────────────────────────────────────{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[DATABASE]{Style.RESET_ALL} Initializing asynchronous SQLite storage...")
        await self.db.initialize()
        print(f"{Fore.GREEN}[DATABASE]{Style.RESET_ALL} Database schema validated and operational.")

        print(f"{Fore.YELLOW}[EXTENSIONS]{Style.RESET_ALL} Loading dynamic cogs...")
        cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                cog_name = f"cogs.{filename[:-3]}"
                try:
                    await self.load_extension(cog_name)
                    print(f"  {Fore.GREEN}✔{Style.RESET_ALL} Loaded extension: {Fore.WHITE}{cog_name}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"  {Fore.RED}✖ Failed to load extension {cog_name}: {e}{Style.RESET_ALL}")

        print(f"{Fore.YELLOW}[SYNC]{Style.RESET_ALL} Synchronizing application slash commands globally...")
        try:
            synced = await self.tree.sync()
            print(f"{Fore.GREEN}[SYNC]{Style.RESET_ALL} Successfully registered {len(synced)} slash commands.")
        except Exception as e:
            print(f"{Fore.RED}[SYNC ERROR]{Style.RESET_ALL} Failed to sync slash commands: {e}")

        self.presence_task.start()

    async def on_ready(self):
        banner = f"""
{Fore.BLUE}  ██████╗ ███████╗███╗   ██╗
  ██╔══██╗██╔════╝████╗  ██║
  ██████╔╝█████╗  ██╔██╗ ██║
  ██╔══██╗██╔══╝  ██║╚██╗██║
  ██████╔╝███████╗██║ ╚████║
  ╚═════╝ ╚══════╝╚═╝  ╚═══╝{Style.RESET_ALL}
{Fore.CYAN}  {config.BOT_NAME} Enterprise Management System • v{config.BOT_VERSION}
  Transparent UI Architecture Active (#2B2D31)
{Fore.CYAN}──────────────────────────────────────────────────{Style.RESET_ALL}
  {Fore.GREEN}● Status      :{Style.RESET_ALL} Online & Connected
  {Fore.GREEN}● Logged In As:{Style.RESET_ALL} {self.user.name} ({self.user.id})
  {Fore.GREEN}● Guild Count :{Style.RESET_ALL} {len(self.guilds)} servers
  {Fore.GREEN}● Python      :{Style.RESET_ALL} {sys.version.split()[0]}
  {Fore.GREEN}● discord.py  :{Style.RESET_ALL} {discord.__version__}
{Fore.CYAN}──────────────────────────────────────────────────{Style.RESET_ALL}
"""
        print(banner)

    @tasks.loop(seconds=30)
    async def presence_task(self):
        """Rotates presence activity dynamically across features."""
        if not self.status_cycle:
            statuses = [
                discord.Activity(type=discord.ActivityType.listening, name=f"/help | {config.BOT_NAME} v{config.BOT_VERSION}"),
                discord.Activity(type=discord.ActivityType.watching, name=f"{len(self.guilds)} servers | Tickets & Logs"),
                discord.Activity(type=discord.ActivityType.playing, name="Music & Mini-Games | /tictactoe"),
                discord.Activity(type=discord.ActivityType.competing, name="Staff Recruitment | /application")
            ]
            self.status_cycle = itertools.cycle(statuses)

        activity = next(self.status_cycle)
        await self.change_presence(status=discord.Status.online, activity=activity)

    @presence_task.before_loop
    async def before_presence_loop(self):
        await self.wait_until_ready()

# Instantiate bot
bot = BenBot()

# --- Global Slash Command Error Handling ---
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        perms = ", ".join(f"`{p}`" for p in error.missing_permissions)
        embed = error_embed("Permission Denied", f"You do not hold the required permissions to execute this command:\n> {perms}")
    elif isinstance(error, app_commands.BotMissingPermissions):
        perms = ", ".join(f"`{p}`" for p in error.missing_permissions)
        embed = error_embed("Bot Permission Fault", f"I require the following permissions to fulfill this operation:\n> {perms}")
    elif isinstance(error, app_commands.CommandOnCooldown):
        embed = error_embed("Cooldown Active", f"Please wait `{error.retry_after:.1f}s` before re-issuing this command.")
    else:
        embed = error_embed("Execution Error", f"An internal error occurred: `{str(error)}`")

    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception:
        pass


def main():
    token = config.BOT_TOKEN
    if not token or token == "YOUR_DISCORD_BOT_TOKEN_HERE":
        print(f"\n{Fore.RED}[CRITICAL ERROR] Bot Token is missing!{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Please open the `.env` file and insert your Discord Bot Token:{Style.RESET_ALL}")
        print(f"DISCORD_TOKEN=your_token_here\n")
        sys.exit(1)

    try:
        bot.run(token)
    except discord.LoginFailure:
        print(f"\n{Fore.RED}[LOGIN FAILED] The provided Discord Bot Token is invalid.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}[FATAL ERROR] An unexpected error occurred: {e}{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
