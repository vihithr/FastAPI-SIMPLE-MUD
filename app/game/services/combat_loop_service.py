"""战斗循环服务 - 处理自动战斗轮次"""
import asyncio
from typing import Dict, Optional
from sqlalchemy.orm import Session
from ...models import Character
from .combat_service import CombatService
from .config_service import ConfigService
from ...websocket.manager import manager


class CombatLoopService:
    """战斗循环服务 - 管理自动战斗轮次"""
    
    def __init__(self, db: Session):
        self.db = db
        self.config_service = ConfigService(db)
        self.combat_service = CombatService(db, self.config_service)
        self.active_combats: Dict[int, asyncio.Task] = {}  # character_id -> combat_task
        self.combat_turn_interval = 3  # 每轮战斗间隔（秒）
    
    async def start_combat(self, attacker: Character, defender: Character) -> Dict:
        """开始战斗循环"""
        # 检查是否已经在战斗中
        if attacker.in_combat_with is not None:
            return {
                "type": "error",
                "message": "你已经在战斗中！"
            }
        
        if defender.in_combat_with is not None:
            return {
                "type": "error",
                "message": f"{defender.name} 正在与其他玩家战斗！"
            }
        
        # 检查双方是否在线
        if attacker.id not in manager.character_to_user:
            return {
                "type": "error",
                "message": "你不在线"
            }
        
        if defender.id not in manager.character_to_user:
            return {
                "type": "error",
                "message": "目标不在线"
            }
        
        # 设置战斗状态
        attacker.in_combat_with = defender.id
        defender.in_combat_with = attacker.id
        attacker.combat_turn = 0
        defender.combat_turn = 0
        self.db.commit()
        
        # 发送战斗开始消息
        start_message = {
            "type": "combat",
            "message": f"战斗开始！你与 {defender.name} 的战斗开始了！",
            "data": {
                "combat_start": True,
                "opponent": defender.name
            }
        }
        
        await manager.send_personal_message(
            start_message,
            manager.character_to_user[attacker.id]
        )
        
        await manager.send_personal_message(
            {
                "type": "combat",
                "message": f"战斗开始！{attacker.name} 向你发起了战斗！",
                "data": {
                    "combat_start": True,
                    "opponent": attacker.name
                }
            },
            manager.character_to_user[defender.id]
        )
        
        # 启动战斗循环任务
        combat_task = asyncio.create_task(
            self._combat_loop(attacker.id, defender.id)
        )
        self.active_combats[attacker.id] = combat_task
        self.active_combats[defender.id] = combat_task
        
        return {
            "type": "combat",
            "message": f"战斗开始！你与 {defender.name} 的战斗开始了！",
            "data": {
                "combat_start": True,
                "opponent": defender.name
            }
        }
    
    async def _combat_loop(self, attacker_id: int, defender_id: int):
        """战斗循环 - 自动轮流攻击"""
        try:
            turn = 0
            while True:
                await asyncio.sleep(self.combat_turn_interval)
                
                # 重新获取角色数据（从数据库刷新）
                attacker = self.db.query(Character).filter(Character.id == attacker_id).first()
                defender = self.db.query(Character).filter(Character.id == defender_id).first()
                
                if not attacker or not defender:
                    break
                
                # 检查战斗状态是否仍然有效
                if attacker.in_combat_with != defender_id or defender.in_combat_with != attacker_id:
                    break
                
                # 检查双方是否在线
                if attacker.id not in manager.character_to_user:
                    await self._end_combat(attacker, defender, reason="attacker_offline")
                    break
                
                if defender.id not in manager.character_to_user:
                    await self._end_combat(attacker, defender, reason="defender_offline")
                    break
                
                # 检查是否有人死亡
                if attacker.hp <= 0:
                    await self._end_combat(attacker, defender, reason="attacker_dead")
                    break
                
                if defender.hp <= 0:
                    await self._end_combat(attacker, defender, reason="defender_dead")
                    break
                
                # 执行攻击（轮流）
                if turn % 2 == 0:
                    # 攻击者回合
                    result = self.combat_service.attack_character(attacker, defender.name, start_combat_loop=False)
                    if result.get("type") == "combat":
                        await self._send_combat_result(result, attacker, defender)
                else:
                    # 防御者回合（反击）
                    result = self.combat_service.attack_character(defender, attacker.name, start_combat_loop=False)
                    if result.get("type") == "combat":
                        await self._send_combat_result(result, defender, attacker)
                
                turn += 1
                attacker.combat_turn = turn
                defender.combat_turn = turn
                self.db.commit()
                
        except Exception as e:
            print(f"Error in combat loop: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 清理战斗状态
            self._cleanup_combat(attacker_id, defender_id)
    
    async def _send_combat_result(self, result: Dict, attacker: Character, defender: Character):
        """发送战斗结果消息"""
        attacker_user_id = manager.character_to_user.get(attacker.id)
        defender_user_id = manager.character_to_user.get(defender.id)
        
        if attacker_user_id:
            await manager.send_personal_message(result, attacker_user_id)
        
        if defender_user_id and result.get("defender_message"):
            await manager.send_personal_message({
                "type": "combat",
                "message": result["defender_message"],
                "data": result.get("data", {})
            }, defender_user_id)
        
        # 广播到房间
        if attacker.room_id:
            await manager.broadcast_to_room(
                {
                    "type": "combat",
                    "message": f"{attacker.name} 攻击了 {defender.name}！",
                    "data": result.get("data", {})
                },
                attacker.room_id,
                exclude_character_id=attacker.id,
                db=self.db
            )
    
    async def _end_combat(self, attacker: Character, defender: Character, reason: str):
        """结束战斗"""
        messages = {
            "attacker_dead": {
                "attacker": f"你被 {defender.name} 击败了！",
                "defender": f"你击败了 {attacker.name}！"
            },
            "defender_dead": {
                "attacker": f"你击败了 {defender.name}！",
                "defender": f"你被 {attacker.name} 击败了！"
            },
            "attacker_offline": {
                "attacker": "",
                "defender": f"{attacker.name} 离开了战斗。"
            },
            "defender_offline": {
                "attacker": f"{defender.name} 离开了战斗。",
                "defender": ""
            },
            "flee": {
                "attacker": f"你逃离了与 {defender.name} 的战斗。",
                "defender": f"{attacker.name} 逃离了战斗。"
            }
        }
        
        msg = messages.get(reason, {"attacker": "战斗结束", "defender": "战斗结束"})
        
        attacker_user_id = manager.character_to_user.get(attacker.id)
        defender_user_id = manager.character_to_user.get(defender.id)
        
        if attacker_user_id and msg["attacker"]:
            await manager.send_personal_message({
                "type": "combat",
                "message": msg["attacker"],
                "data": {"combat_end": True}
            }, attacker_user_id)
        
        if defender_user_id and msg["defender"]:
            await manager.send_personal_message({
                "type": "combat",
                "message": msg["defender"],
                "data": {"combat_end": True}
            }, defender_user_id)
        
        self._cleanup_combat(attacker.id, defender.id)
    
    def _cleanup_combat(self, attacker_id: int, defender_id: int):
        """清理战斗状态"""
        attacker = self.db.query(Character).filter(Character.id == attacker_id).first()
        defender = self.db.query(Character).filter(Character.id == defender_id).first()
        
        if attacker:
            attacker.in_combat_with = None
            attacker.combat_turn = 0
        
        if defender:
            defender.in_combat_with = None
            defender.combat_turn = 0
        
        self.db.commit()
        
        # 取消战斗任务
        if attacker_id in self.active_combats:
            task = self.active_combats[attacker_id]
            if not task.done():
                task.cancel()
            del self.active_combats[attacker_id]
        
        if defender_id in self.active_combats:
            task = self.active_combats[defender_id]
            if not task.done():
                task.cancel()
            del self.active_combats[defender_id]
    
    async def stop_combat(self, character: Character) -> Dict:
        """停止战斗（逃跑）"""
        # 刷新角色数据
        character = self.db.query(Character).filter(Character.id == character.id).first()
        
        if not character or character.in_combat_with is None:
            return {
                "type": "error",
                "message": "你不在战斗中"
            }
        
        opponent_id = character.in_combat_with
        opponent = self.db.query(Character).filter(Character.id == opponent_id).first()
        
        if opponent:
            await self._end_combat(character, opponent, reason="flee")
            return {
                "type": "info",
                "message": f"你逃离了与 {opponent.name} 的战斗"
            }
        
        return {
            "type": "error",
            "message": "无法找到战斗对手"
        }

