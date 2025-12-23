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
        
        # 检查是否是测试靶子
        from ...repositories.room_repository import RoomRepository
        from ...repositories.npc_repository import NPCRepository
        room_repo = RoomRepository(db)
        npc_repo = NPCRepository(db)
        
        if character.room_id:
            room = room_repo.get_by_id(character.room_id)
            if room:
                training_dummy = npc_repo.get_training_dummy_in_room(room.id)
                if training_dummy and target_name.lower() in ["测试靶子", "靶子", "dummy", "target", training_dummy.name.lower()]:
                    # 处理测试靶子攻击
                    combat_loop = CombatLoopService(db)
                    
                    # 检查是否已经在训练中
                    if character.in_combat_with is not None and character.in_combat_with < 0:
                        # 已经在训练中，提示用户
                        result = {
                            "type": "info",
                            "message": "你正在训练中，战斗会自动进行。使用 'flee' 命令可以停止训练。"
                        }
                    else:
                        # 不在训练中，启动训练循环
                        result = await combat_loop.start_training_dummy_combat(character, training_dummy)
                    
                    return result
        
        # 处理玩家之间的战斗
        # 检查是否已经在战斗中
        if character.in_combat_with is not None and character.in_combat_with > 0:
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
