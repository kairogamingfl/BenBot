"""
BEN Discord Bot - Audio & Music Entertainment System
Features voice streaming, playlist queuing, and an interactive playback control dashboard (Buttons).
"""
import asyncio
from typing import Optional, List, Dict, Any
import discord
from discord import app_commands, ui
from discord.ext import commands
import yt_dlp
from utils.embeds import BenEmbed, success_embed, error_embed, info_embed
import config

# yt-dlp extraction configuration
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

class Track:
    def __init__(self, data: dict, requester: discord.Member):
        self.data = data
        self.requester = requester
        self.title = data.get('title', 'Unknown Track')
        self.url = data.get('url')
        self.webpage_url = data.get('webpage_url', '')
        self.duration = data.get('duration', 0)
        self.thumbnail = data.get('thumbnail')
        self.uploader = data.get('uploader', 'Unknown Artist')

    def formatted_duration(self) -> str:
        if not self.duration:
            return "Live Stream"
        minutes, seconds = divmod(self.duration, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"


class MusicPlayerView(ui.View):
    """Interactive Player Dashboard with Pause, Skip, Stop, Queue controls."""
    def __init__(self, cog: "Music", guild_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id

    @ui.button(emoji="⏯️", style=discord.ButtonStyle.secondary, custom_id="ben:music_pause")
    async def toggle_play(self, interaction: discord.Interaction, button: ui.Button):
        vc = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("I am not connected to a voice channel.", ephemeral=True)
            return

        if vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸️ Playback paused.", ephemeral=True)
        elif vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶️ Playback resumed.", ephemeral=True)
        else:
            await interaction.response.send_message("No active track is loaded.", ephemeral=True)

    @ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, custom_id="ben:music_skip")
    async def skip_track(self, interaction: discord.Interaction, button: ui.Button):
        vc = interaction.guild.voice_client
        if not vc or not vc.is_playing():
            await interaction.response.send_message("Nothing is currently playing.", ephemeral=True)
            return
        vc.stop() # Trigger after_play callback which advances queue
        await interaction.response.send_message("⏭️ Skipped to the next track.", ephemeral=True)

    @ui.button(emoji="⏹️", style=discord.ButtonStyle.danger, custom_id="ben:music_stop")
    async def stop_player(self, interaction: discord.Interaction, button: ui.Button):
        vc = interaction.guild.voice_client
        if vc:
            queue = self.cog.get_queue(self.guild_id)
            queue.clear()
            await vc.disconnect()
            await interaction.response.send_message("⏹️ Playback terminated and queue flushed.", ephemeral=True)
        else:
            await interaction.response.send_message("Not connected to voice.", ephemeral=True)

    @ui.button(emoji="📋", style=discord.ButtonStyle.secondary, custom_id="ben:music_queue")
    async def show_queue(self, interaction: discord.Interaction, button: ui.Button):
        queue = self.cog.get_queue(self.guild_id)
        current = self.cog.get_current_track(self.guild_id)

        if not current and not queue:
            await interaction.response.send_message("The playback queue is currently empty.", ephemeral=True)
            return

        lines = []
        if current:
            lines.append(f"**Now Playing**: [{current.title}]({current.webpage_url}) `[{current.formatted_duration()}]`")
            lines.append("──────────────────────────────")

        if queue:
            for idx, track in enumerate(queue[:10], start=1):
                lines.append(f"`{idx:02d}.` [{track.title}]({track.webpage_url}) `[{track.formatted_duration()}]` • {track.requester.mention}")
            if len(queue) > 10:
                lines.append(f"*...and {len(queue) - 10} more tracks in queue.*")
        else:
            lines.append("*No upcoming tracks waiting in queue.*")

        embed = BenEmbed(
            title="📋  CURRENT PLAYLIST QUEUE",
            description="\n".join(lines),
            color=config.COLOR_TRANSPARENT
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues: Dict[int, List[Track]] = {}
        self.current_tracks: Dict[int, Optional[Track]] = {}

    def get_queue(self, guild_id: int) -> List[Track]:
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]

    def get_current_track(self, guild_id: int) -> Optional[Track]:
        return self.current_tracks.get(guild_id)

    async def extract_track(self, query: str, requester: discord.Member) -> Optional[Track]:
        loop = asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))
            if 'entries' in data:
                data = data['entries'][0]
            return Track(data, requester)
        except Exception:
            return None

    def play_next(self, guild: discord.Guild, channel: discord.TextChannel):
        queue = self.get_queue(guild.id)
        vc = guild.voice_client

        if not vc or not vc.is_connected():
            return

        if not queue:
            self.current_tracks[guild.id] = None
            asyncio.run_coroutine_threadsafe(
                channel.send(
                    embed=info_embed("Queue Concluded", "Playlist reached the end. Add more tracks with `/play`.")
                ),
                self.bot.loop
            )
            return

        track = queue.pop(0)
        self.current_tracks[guild.id] = track

        try:
            source = discord.FFmpegPCMAudio(track.url, **FFMPEG_OPTIONS)
            transformer = discord.PCMVolumeTransformer(source, volume=0.8)

            def after_play(error):
                if error:
                    print(f"Player Error: {error}")
                self.play_next(guild, channel)

            vc.play(transformer, after=after_play)

            embed = BenEmbed(
                title="🎵  NOW PLAYING",
                description=(
                    f"### [{track.title}]({track.webpage_url}) ✦\n"
                    f"> **Artist / Channel**: `{track.uploader}`\n\n"
                    f"{config.EMOJIS['bullet']} **Duration**: `{track.formatted_duration()}`\n"
                    f"{config.EMOJIS['bullet']} **Requested By**: {track.requester.mention}\n"
                    f"{config.EMOJIS['bullet']} **Audio Stream**: `Direct 320kbps High Fidelity`\n"
                ),
                color=config.COLOR_TRANSPARENT,
                thumbnail=track.thumbnail
            )
            view = MusicPlayerView(self, guild.id)
            asyncio.run_coroutine_threadsafe(
                channel.send(embed=embed, view=view),
                self.bot.loop
            )
        except Exception as e:
            asyncio.run_coroutine_threadsafe(
                channel.send(
                    embed=error_embed("Playback Error", f"Audio player encountered an issue: `{e}`.\n*(Ensure FFmpeg is installed)*")
                ),
                self.bot.loop
            )
            self.play_next(guild, channel)

    music_group = app_commands.Group(name="music", description="Stream high-quality audio and control playlist")

    @music_group.command(name="play", description="Search and stream audio from YouTube / URL into your voice channel")
    @app_commands.describe(query="Song title, artist, or direct media URL")
    async def play(self, interaction: discord.Interaction, query: str):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message(
                embed=error_embed("Voice Required", "Please enter a voice channel first before playing music."),
                ephemeral=True
            )
            return

        user_channel = interaction.user.voice.channel
        vc = interaction.guild.voice_client

        await interaction.response.defer()

        # Connect or move
        if not vc:
            try:
                vc = await user_channel.connect()
            except Exception as e:
                await interaction.followup.send(embed=error_embed("Connection Failed", f"Could not join voice: `{e}`"))
                return
        elif vc.channel != user_channel:
            await vc.move_to(user_channel)

        track = await self.extract_track(query, interaction.user)
        if not track:
            await interaction.followup.send(
                embed=error_embed("Search Failure", f"Could not locate an audio stream matching: `{query}`.")
            )
            return

        queue = self.get_queue(interaction.guild_id)

        if vc.is_playing() or vc.is_paused():
            queue.append(track)
            embed = BenEmbed(
                title="📋  TRACK ADDED TO QUEUE",
                description=(
                    f"### [{track.title}]({track.webpage_url}) ✦\n"
                    f"{config.EMOJIS['bullet']} **Position in Queue**: `#{len(queue)}`\n"
                    f"{config.EMOJIS['bullet']} **Duration**: `{track.formatted_duration()}`\n"
                    f"{config.EMOJIS['bullet']} **Requested By**: {interaction.user.mention}\n"
                ),
                color=config.COLOR_TRANSPARENT,
                thumbnail=track.thumbnail
            )
            await interaction.followup.send(embed=embed)
        else:
            queue.append(track)
            await interaction.followup.send(
                embed=success_embed("Starting Stream", f"Loaded **{track.title}** into player.")
            )
            self.play_next(interaction.guild, interaction.channel)

    @music_group.command(name="skip", description="Skip to the next song in the queue")
    async def skip(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc or not vc.is_playing():
            await interaction.response.send_message(embed=error_embed("Idle", "No audio is currently playing."), ephemeral=True)
            return
        vc.stop()
        await interaction.response.send_message(embed=success_embed("Track Skipped", "Advanced to next item in queue."))

    @music_group.command(name="stop", description="Stop music and clear the entire playlist")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            self.get_queue(interaction.guild_id).clear()
            self.current_tracks[interaction.guild_id] = None
            await vc.disconnect()
            await interaction.response.send_message(embed=success_embed("Playback Stopped", "Audio terminated and queue cleared."))
        else:
            await interaction.response.send_message(embed=error_embed("Disconnected", "Not connected to a voice channel."), ephemeral=True)

    @music_group.command(name="queue", description="Display the current playback queue")
    async def queue_cmd(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild_id)
        current = self.get_current_track(interaction.guild_id)

        if not current and not queue:
            await interaction.response.send_message(embed=info_embed("Queue Empty", "No songs currently in the queue."), ephemeral=True)
            return

        lines = []
        if current:
            lines.append(f"**Now Playing**: [{current.title}]({current.webpage_url}) `[{current.formatted_duration()}]`")
            lines.append("──────────────────────────────")

        for idx, track in enumerate(queue[:10], start=1):
            lines.append(f"`{idx:02d}.` [{track.title}]({track.webpage_url}) `[{track.formatted_duration()}]` • {track.requester.mention}")

        if len(queue) > 10:
            lines.append(f"\n*+{len(queue) - 10} additional tracks waiting in queue.*")

        embed = BenEmbed(
            title="📋  MUSIC QUEUE",
            description="\n".join(lines),
            color=config.COLOR_TRANSPARENT
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
