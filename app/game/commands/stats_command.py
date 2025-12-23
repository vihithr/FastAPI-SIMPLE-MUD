"""属性查看命令"""
from typing import Dict
from sqlalchemy.orm import Session
from ...models import Character
from .base_command import Command
from ..services.character_service import CharacterService


class StatsCommand(Command):
    """查看角色属性命令"""
    
    def __init__(self):
        super().__init__("stats", ["status", "stat"])
    
    async def execute(
        self,
        db: Session,
        character: Character,
        args: list,
        **kwargs
    ) -> Dict:
        """执行查看属性命令"""
        character_service = CharacterService(db)
        return character_service.get_character_stats(character)
