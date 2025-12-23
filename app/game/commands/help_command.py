"""帮助命令"""
from typing import Dict
from sqlalchemy.orm import Session
from ...models import Character
from .base_command import Command
from ..services.room_service import RoomService


class HelpCommand(Command):
    """帮助命令"""
    
    def __init__(self):
        super().__init__("help", ["h", "?"])
    
    async def execute(
        self,
        db: Session,
        character: Character,
        args: list,
        **kwargs
    ) -> Dict:
        """执行帮助命令"""
        room_service = RoomService(db)
        available = room_service.get_available_commands(character)
        
        help_lines = [
            "可用命令:",
            f"  移动: {', '.join(available.get('movement') or ['无'])}",
            "  查看: look(l), stats, inventory(inv), equipment(eq)",
            "  战斗: attack <目标>",
            "  物品: equip <物品>, unequip <槽位>, use <物品>",
            "  社交: say <消息>",
        ]
        if available.get("room"):
            help_lines.append(f"  房间: {', '.join(available['room'])}")
        
        return {
            "type": "info",
            "message": "\n".join(help_lines)
        }
