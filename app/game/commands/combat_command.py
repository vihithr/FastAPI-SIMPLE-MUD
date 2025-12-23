"""战斗命令"""
from typing import Dict
from sqlalchemy.orm import Session
from ...models import Character
from .base_command import Command
from ..services.combat_service import CombatService
from ..services.config_service import ConfigService


class CombatCommand(Command):
    """战斗命令"""
    
    def __init__(self):
        super().__init__("attack", ["hit", "fight"])
    
    async def execute(
        self,
        db: Session,
        character: Character,
        args: list,
        **kwargs
    ) -> Dict:
        """执行攻击命令"""
        if not args:
            return {
                "type": "error",
                "message": "请指定攻击目标。用法: attack <目标名称>"
            }
        
        target_name = " ".join(args)
        config_service = ConfigService(db)
        combat_service = CombatService(db, config_service)
        result = combat_service.attack_character(character, target_name)
        
        return result
