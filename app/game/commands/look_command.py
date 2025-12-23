"""查看命令"""
from typing import Dict
from sqlalchemy.orm import Session
from ...models import Character
from .base_command import Command
from ..services.character_service import CharacterService


class LookCommand(Command):
    """查看房间命令"""
    
    def __init__(self):
        super().__init__("look", ["l"])
    
    async def execute(
        self,
        db: Session,
        character: Character,
        args: list,
        **kwargs
    ) -> Dict:
        """执行查看命令"""
        character_service = CharacterService(db)
        result = character_service.look_room(character)
        return result
