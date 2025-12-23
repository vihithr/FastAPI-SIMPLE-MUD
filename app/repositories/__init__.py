"""Repository层 - 数据访问抽象"""
from .base_repository import BaseRepository
from .character_repository import CharacterRepository
from .item_repository import ItemRepository
from .room_repository import RoomRepository
from .config_repository import ConfigRepository
from .npc_repository import NPCRepository

__all__ = [
    "BaseRepository",
    "CharacterRepository",
    "ItemRepository",
    "RoomRepository",
    "ConfigRepository",
    "NPCRepository",
]
