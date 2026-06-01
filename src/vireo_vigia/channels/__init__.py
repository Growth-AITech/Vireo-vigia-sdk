"""Output channel adapters."""

from vireo_vigia.channels.base import ChannelAdapter
from vireo_vigia.channels.discord import DiscordChannelAdapter
from vireo_vigia.channels.telegram import TelegramChannelAdapter

__all__ = [
    "ChannelAdapter",
    "DiscordChannelAdapter",
    "TelegramChannelAdapter",
]
