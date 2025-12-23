"""移动命令"""
from typing import Dict
from sqlalchemy.orm import Session
from ...models import Character
from .base_command import Command
from ..services.character_service import CharacterService


class MovementCommand(Command):
    """移动命令"""
    
    def __init__(self):
        super().__init__("move", ["north", "n", "south", "s", "east", "e", "west", "w"])
    
    async def execute(
        self,
        db: Session,
        character: Character,
        args: list,
        **kwargs
    ) -> Dict:
        """执行移动命令"""
        if not args:
            return {
                "type": "error",
                "message": "请指定移动方向。用法: north(n), south(s), east(e), west(w)"
            }
        
        direction = args[0].lower()
        character_service = CharacterService(db)
        result = character_service.move_character(character, direction)
        
        if result["type"] == "success":
            # 附带当前可用指令
            from ..services.room_service import RoomService
            room_service = RoomService(db)
            result.setdefault("data", {})
            result["data"]["available_commands"] = room_service.get_available_commands(character)
        
        return result
