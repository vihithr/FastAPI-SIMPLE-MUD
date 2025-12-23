"""战斗服务 - 业务逻辑层"""
import random
from typing import Dict, Tuple, Optional, TYPE_CHECKING
from sqlalchemy.orm import Session
from ...models import Character, CombatLog
from ...repositories.character_repository import CharacterRepository
from ...repositories.npc_repository import NPCRepository
from ...repositories.room_repository import RoomRepository
from .config_service import ConfigService

if TYPE_CHECKING:
    from ...models import NPC


def roll_dice(sides: int, count: int = 1) -> int:
    """掷骰子（纯函数）"""
    return sum(random.randint(1, sides) for _ in range(count))


def roll_to_hit(
    attacker_attack: int,
    defender_defense: int,
    attack_modifier_ratio: float = 0.5
) -> Tuple[bool, int, bool]:
    """
    掷骰判定命中（纯函数，使用配置参数）
    返回: (是否命中, 掷骰结果, 是否暴击)
    """
    d20_roll = roll_dice(20, 1)
    attack_modifier = int(attacker_attack * attack_modifier_ratio)
    total_roll = d20_roll + attack_modifier
    
    # 自然1必定失误
    if d20_roll == 1:
        return False, total_roll, False
    
    # 自然20必定命中且暴击
    if d20_roll == 20:
        return True, total_roll, True
    
    # 普通命中判定: 总结果 >= 防御力 + 10
    target_ac = defender_defense + 10
    hit = total_roll >= target_ac
    
    return hit, total_roll, False


def roll_damage(
    attacker_attack: int,
    is_critical: bool = False,
    damage_modifier_ratio: float = 0.33
) -> int:
    """
    掷骰计算伤害（纯函数，使用配置参数）
    """
    # 基础伤害骰: 1d(攻击力)，最小为1d4
    damage_die = max(4, attacker_attack)
    base_damage = roll_dice(damage_die, 1)
    
    # 攻击力修正
    attack_modifier = max(1, int(attacker_attack * damage_modifier_ratio))
    
    total_damage = base_damage + attack_modifier
    
    # 暴击伤害翻倍
    if is_critical:
        total_damage *= 2
    
    return max(1, total_damage)


def apply_defense_reduction(
    damage: int,
    defender_defense: int,
    defense_reduction_ratio: float = 0.5
) -> int:
    """
    应用防御减免（纯函数，使用配置参数）
    """
    defense_reduction = int(defender_defense * defense_reduction_ratio)
    final_damage = max(1, damage - defense_reduction)
    return final_damage


def resolve_attack(
    attacker_attack: int,
    defender_defense: int,
    defender_hp: int,
    defender_max_hp: int,
    combat_config: Dict[str, float]
) -> Dict:
    """
    解析一次攻击 (完全无状态，使用配置参数)
    
    返回战斗结果字典，包含:
    - hit: 是否命中
    - critical: 是否暴击
    - damage: 造成的伤害
    - roll_result: 命中掷骰结果
    - defender_hp_after: 防御者剩余生命值
    """
    attack_modifier_ratio = combat_config.get("attack_modifier_ratio", 0.5)
    defense_reduction_ratio = combat_config.get("defense_reduction_ratio", 0.5)
    damage_modifier_ratio = combat_config.get("damage_modifier_ratio", 0.33)
    
    # 掷骰判定命中
    hit, roll_result, is_critical = roll_to_hit(
        attacker_attack,
        defender_defense,
        attack_modifier_ratio
    )
    
    if not hit:
        return {
            "hit": False,
            "critical": False,
            "damage": 0,
            "roll_result": roll_result,
            "defender_hp_after": defender_hp,
            "miss": True
        }
    
    # 计算伤害
    damage = roll_damage(attacker_attack, is_critical, damage_modifier_ratio)
    
    # 应用防御减免
    final_damage = apply_defense_reduction(damage, defender_defense, defense_reduction_ratio)
    
    # 计算剩余生命值
    defender_hp_after = max(0, defender_hp - final_damage)
    
    return {
        "hit": True,
        "critical": is_critical,
        "damage": final_damage,
        "roll_result": roll_result,
        "defender_hp_after": defender_hp_after,
        "miss": False
    }


class CombatService:
    """战斗服务 - 处理战斗相关的业务逻辑"""
    
    def __init__(self, db: Session, config_service: ConfigService):
        self.db = db
        self.config_service = config_service
        self.character_repo = CharacterRepository(db)
        self.npc_repo = NPCRepository(db)
        self.room_repo = RoomRepository(db)
    
    def attack_character(
        self,
        attacker: Character,
        defender_name: str,
        start_combat_loop: bool = False
    ) -> Dict:
        """攻击目标角色"""
        # 获取战斗配置
        combat_config = self.config_service.get_combat_config()
        
        # 检查是否在同一房间
        if attacker.room_id is None:
            return {
                "type": "error",
                "message": "无法获取房间信息"
            }
        
        room = self.room_repo.get_by_id(attacker.room_id)
        if not room:
            return {
                "type": "error",
                "message": "无法获取房间信息"
            }
        
        # 检查是否是训练靶子
        training_dummy = self.npc_repo.get_training_dummy_in_room(room.id)
        if training_dummy and defender_name.lower() in ["测试靶子", "靶子", "dummy", "target", training_dummy.name.lower()]:
            return self.attack_training_dummy(attacker, training_dummy, combat_config)
        
        # 获取房间内的其他角色
        from ...websocket.manager import manager
        online_players = manager.get_online_characters_in_room(room.id, self.db)
        defender_info = None
        for p in online_players:
            if p["name"].lower() == defender_name.lower() and p["id"] != attacker.id:
                defender_info = p
                break
        
        if not defender_info:
            if attacker.name.lower() == defender_name.lower():
                return {
                    "type": "error",
                    "message": "你不能攻击自己！"
                }
            
            if training_dummy:
                return {
                    "type": "error",
                    "message": f"找不到目标 '{defender_name}'。在训练场，你可以攻击 '测试靶子' 来练习。"
                }
            
            return {
                "type": "error",
                "message": f"找不到目标 '{defender_name}' 或目标不在同一房间"
            }
        
        defender = self.character_repo.get_by_id(defender_info["id"])
        if not defender:
            return {
                "type": "error",
                "message": f"找不到目标 '{defender_name}'"
            }
        
        # 防止攻击自己
        if attacker.id == defender.id:
            return {
                "type": "error",
                "message": "你不能攻击自己！"
            }
        
        # 检查是否在同一房间
        if attacker.room_id != defender.room_id:
            return {
                "type": "error",
                "message": "目标不在同一房间"
            }
        
        # 检查目标是否在线
        from ...websocket.manager import manager
        if defender.id not in manager.character_to_user:
            return {
                "type": "error",
                "message": "目标不在线"
            }
        
        # 如果指定启动战斗循环，且双方都不在战斗中，则启动战斗循环
        if start_combat_loop and attacker.in_combat_with is None and defender.in_combat_with is None:
            from .combat_loop_service import CombatLoopService
            combat_loop = CombatLoopService(self.db)
            # 注意：这里需要异步调用，但当前方法是同步的
            # 我们将在CombatCommand中处理异步调用
            return {
                "type": "combat",
                "message": f"开始与 {defender.name} 的战斗！",
                "data": {
                    "start_combat_loop": True,
                    "attacker_id": attacker.id,
                    "defender_id": defender.id
                }
            }
        
        # 使用无状态函数解析攻击
        combat_result = resolve_attack(
            attacker_attack=attacker.attack,
            defender_defense=defender.defense,
            defender_hp=defender.hp,
            defender_max_hp=defender.max_hp,
            combat_config=combat_config
        )
        
        # 应用伤害到数据库
        defender.hp = combat_result["defender_hp_after"]
        attacker_hp_after = attacker.hp
        defender_hp_after = defender.hp
        
        # 记录战斗日志
        combat_log = CombatLog(
            attacker_id=attacker.id,
            defender_id=defender.id,
            damage=combat_result["damage"],
            attacker_hp_after=attacker_hp_after,
            defender_hp_after=defender_hp_after
        )
        self.db.add(combat_log)
        
        # 构建消息
        exp_gain = 0
        level_up = False
        
        if combat_result["miss"]:
            attack_message = f"你攻击 {defender.name}，但未命中！(掷骰: {combat_result['roll_result']})"
            defend_message = f"{attacker.name} 攻击你，但未命中！(掷骰: {combat_result['roll_result']})"
        else:
            damage = combat_result["damage"]
            critical_text = " (暴击！)" if combat_result["critical"] else ""
            
            # 如果目标死亡，给予经验值
            if defender.hp <= 0:
                exp_multiplier = combat_config.get("exp_gain_multiplier", 20)
                exp_gain = defender.level * exp_multiplier
                self.character_repo.add_exp(attacker.id, exp_gain)
                level_up = self._check_level_up(attacker)
                
                attack_message = f"你击败了 {defender.name}！造成 {damage} 点伤害{critical_text}！(掷骰: {combat_result['roll_result']})\n获得 {exp_gain} 经验值。"
                if level_up:
                    attack_message += f"\n恭喜！你升级了！当前等级: {attacker.level}"
                
                defend_message = f"{attacker.name} 击败了你！你失去了 {damage} 生命值{critical_text}。\n你被击败了！"
            else:
                attack_message = f"你对 {defender.name} 造成了 {damage} 点伤害{critical_text}！(掷骰: {combat_result['roll_result']}, {defender.name} 剩余生命值: {defender_hp_after}/{defender.max_hp})"
                defend_message = f"{attacker.name} 对你造成了 {damage} 点伤害{critical_text}！(掷骰: {combat_result['roll_result']}, 剩余生命值: {defender_hp_after}/{defender.max_hp})"
        
        # 提交数据库更改
        self.db.commit()
        
        return {
            "type": "combat",
            "message": attack_message,
            "data": {
                "attacker": attacker.name,
                "defender": defender.name,
                "damage": combat_result["damage"],
                "defender_hp": defender_hp_after,
                "exp_gained": exp_gain,
                "level_up": level_up,
                "hit": combat_result["hit"],
                "critical": combat_result["critical"],
                "roll_result": combat_result["roll_result"],
                "miss": combat_result["miss"]
            },
            "defender_message": defend_message,
            "defender_id": defender.id
        }
    
    def attack_training_dummy(
        self,
        attacker: Character,
        dummy: "NPC",
        combat_config: Dict[str, float]
    ) -> Dict:
        """攻击训练场测试靶子"""
        try:
            # 从NPC属性获取测试靶子数据
            dummy_props = dummy.properties or {}
            dummy_defense = dummy_props.get("defense", 0)
            dummy_max_hp = dummy_props.get("max_hp", 1000)
            # 读取当前HP，如果不存在则使用最大HP
            dummy_hp = dummy_props.get("hp", dummy_max_hp)
            
            # 使用无状态函数解析攻击
            combat_result = resolve_attack(
                attacker_attack=attacker.attack,
                defender_defense=dummy_defense,
                defender_hp=dummy_hp,
                defender_max_hp=dummy_max_hp,
                combat_config=combat_config
            )
            
            # 更新测试靶子的HP（即使未命中也要更新，因为可能之前有伤害）
            dummy_hp_after = combat_result["defender_hp_after"]
            was_destroyed = False
            
            # 如果测试靶子HP降到0或以下，自动恢复到满血（因为测试靶子是无敌的）
            if dummy_hp_after <= 0:
                was_destroyed = True
                dummy_hp_after = dummy_max_hp
            
            dummy_props["hp"] = dummy_hp_after
            dummy.properties = dummy_props
            # 标记对象为已修改，确保SQLAlchemy会保存更改
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(dummy, "properties")
            
            # 构建消息
            if combat_result["miss"]:
                attack_message = f"你攻击测试靶子，但未命中！(掷骰: {combat_result['roll_result']})"
                exp_gain = 1  # 未命中也给少量经验
            else:
                damage = combat_result["damage"]
                critical_text = " (暴击！)" if combat_result["critical"] else ""
                if was_destroyed:
                    attack_message = f"你对测试靶子造成了 {damage} 点伤害{critical_text}！(掷骰: {combat_result['roll_result']})\n测试靶子被摧毁，但立即恢复了！"
                else:
                    attack_message = f"你对测试靶子造成了 {damage} 点伤害{critical_text}！(掷骰: {combat_result['roll_result']}, 测试靶子剩余生命值: {dummy_hp_after}/{dummy_max_hp})"
                exp_gain = 5  # 命中给更多经验
            
            # 给予经验值（训练奖励）
            self.character_repo.add_exp(attacker.id, exp_gain)
            
            # 检查升级
            level_up = False
            try:
                level_up = self._check_level_up(attacker)
            except Exception as e:
                print(f"Error in check_level_up during training dummy attack: {e}")
                self.db.commit()
            
            # 提交所有更改（包括NPC的HP更新）
            if not level_up:
                try:
                    self.db.commit()
                except Exception as e:
                    print(f"Error committing exp gain: {e}")
                    self.db.rollback()
                    raise
            
            if level_up:
                attack_message += f"\n恭喜！你升级了！当前等级: {attacker.level}"
            attack_message += f"\n获得 {exp_gain} 点训练经验。"
            
            return {
                "type": "combat",
                "message": attack_message,
                "data": {
                    "attacker": attacker.name,
                    "defender": "测试靶子",
                    "damage": combat_result["damage"],
                    "defender_hp": dummy_hp_after,
                    "defender_max_hp": dummy_max_hp,
                    "exp_gained": exp_gain,
                    "level_up": level_up,
                    "is_training_dummy": True,
                    "hit": combat_result["hit"],
                    "critical": combat_result["critical"],
                    "roll_result": combat_result["roll_result"],
                    "miss": combat_result["miss"]
                }
            }
        except Exception as e:
            try:
                self.db.rollback()
            except:
                pass
            print(f"Error in attack_training_dummy: {e}")
            import traceback
            traceback.print_exc()
            return {
                "type": "error",
                "message": f"攻击测试靶子时发生错误: {str(e)}"
            }
    
    def _check_level_up(self, character: Character) -> bool:
        """检查并处理升级"""
        try:
            leveling_config = self.config_service.get_leveling_config()
            exp_per_level = leveling_config.get("exp_per_level", 100)
            exp_needed = character.level * exp_per_level
            
            if character.exp >= exp_needed:
                character.level += 1
                character.max_hp += leveling_config.get("hp_per_level", 20)
                character.hp = character.max_hp  # 升级时恢复满血
                character.max_mp += leveling_config.get("mp_per_level", 10)
                character.mp = character.max_mp  # 升级时恢复满魔
                character.attack += leveling_config.get("attack_per_level", 2)
                character.defense += leveling_config.get("defense_per_level", 1)
                self.db.commit()
                return True
            
            return False
        except Exception as e:
            print(f"Error in check_level_up: {e}")
            import traceback
            traceback.print_exc()
            self.db.rollback()
            return False
    
    def heal_character(self, character: Character, amount: int) -> Dict:
        """治疗角色"""
        old_hp = character.hp
        character.hp = min(character.max_hp, character.hp + amount)
        healed = character.hp - old_hp
        self.db.commit()
        
        return {
            "type": "success",
            "message": f"你恢复了 {healed} 点生命值！(当前: {character.hp}/{character.max_hp})",
            "data": {
                "healed": healed,
                "hp": character.hp,
                "max_hp": character.max_hp
            }
        }
