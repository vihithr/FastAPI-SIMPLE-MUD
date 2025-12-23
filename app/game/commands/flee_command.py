"""逃跑命令"""
from typing import Dict
from sqlalchemy.orm import Session
from ...models import Character
from .base_command import Command
from ..services.combat_loop_service import CombatLoopService


class FleeCommand(Command):
    """逃跑命令 - 退出战斗"""
    
    def __init__(self):
        super().__init__("flee", ["run", "escape", "stop"])
    
    async def execute(
        self,
        db: Session,
        character: Character,
        args: list,
        **kwargs
    ) -> Dict:
        """执行逃跑命令"""
        combat_loop = CombatLoopService(db)
        result = await combat_loop.stop_combat(character)
        return result

