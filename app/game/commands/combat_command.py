"""战斗命令"""
from typing import Dict
from sqlalchemy.orm import Session
from ...models import Character
from .base_command import Command
from ..services.combat_service import CombatService
from ..services.config_service import ConfigService
from ..services.combat_loop_service import CombatLoopService


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
        
        # 检查是否已经在战斗中
        if character.in_combat_with is not None:
            # 如果已经在战斗中，执行单次攻击
            result = combat_service.attack_character(character, target_name, start_combat_loop=False)
        else:
            # 如果不在战斗中，启动战斗循环
            result = combat_service.attack_character(character, target_name, start_combat_loop=True)
            
            # 如果返回需要启动战斗循环的信号，则启动
            if result.get("data", {}).get("start_combat_loop"):
                from ...repositories.character_repository import CharacterRepository
                character_repo = CharacterRepository(db)
                defender_id = result["data"]["defender_id"]
                defender = character_repo.get_by_id(defender_id)
                
                if defender:
                    combat_loop = CombatLoopService(db)
                    result = await combat_loop.start_combat(character, defender)
        
        return result
