"""
BEN Discord Bot - Embed Generator
Implements professional transparent (Discord Dark Theme #2B2D31) embeds with elegant typography.
"""
from typing import Optional, Any
import discord
import config
class BenEmbed(discord.Embed):
    """
    Custom Discord Embed styled with the iconic #2B2D31 Dark Theme background.
    Gives a sleek borderless/transparent appearance inside the Discord client.
    """
    def __init__(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        color: int = config.COLOR_TRANSPARENT,
        thumbnail: Optional[str] = None,
        image: Optional[str] = None,
        author_name: Optional[str] = None,
        author_icon: Optional[str] = None,
        author_url: Optional[str] = None,
        footer_text: Optional[str] = None,
        footer_icon: Optional[str] = None,
        timestamp: bool = True,
        **kwargs: Any
    ):
        super().__init__(
            title=title,
            description=description,
            color=color,
            **kwargs
        )
        if author_name:
            self.set_author(name=author_name, icon_url=author_icon, url=author_url)
        if thumbnail:
            self.set_thumbnail(url=thumbnail)
        if image:
            self.set_image(url=image)
        footer = footer_text or config.BOT_FOOTER
        self.set_footer(text=footer, icon_url=footer_icon)
        if timestamp:
            self.timestamp = discord.utils.utcnow()
          
