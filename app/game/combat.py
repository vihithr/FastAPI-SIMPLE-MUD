"""战斗系统"""
import random
from sqlalchemy.orm import Session
from ..models import Character, CombatLog
from ..websocket.manager import manager


def calculate_damage(attacker: Character, defender: Character = None, defender_defense: int = 0) -> int:
    """计算伤害"""
    base_damage = attacker.attack
    # 添加随机波动 (80% - 120%)
    damage_multiplier = random.uniform(0.8, 1.2)
    damage = int(base_damage * damage_multiplier)
    
    # 防御减免
    if defender:
        defense_reduction = defender.defense * 0.5
    else:
        defense_reduction = defender_defense * 0.5
    final_damage = max(1, int(damage - defense_reduction))
    
    return final_damage


def attack_training_dummy(db: Session, attacker: Character) -> dict:
    """攻击训练场测试靶子"""
    # 测试靶子属性：高血量，低防御，不会反击
    dummy_defense = 0
    dummy_max_hp = 1000
    dummy_hp = dummy_max_hp  # 测试靶子总是满血
    
    # 计算伤害
    damage = calculate_damage(attacker, defender_defense=dummy_defense)
    
    # 给予少量经验值（训练奖励）
    exp_gain = 5
    attacker.exp += exp_gain
    level_up = check_level_up(db, attacker)
    
    db.commit()
    
    attack_message = f"你对测试靶子造成了 {damage} 点伤害！(测试靶子剩余生命值: {dummy_hp - damage}/{dummy_max_hp})\n获得 {exp_gain} 点训练经验。"
    if level_up:
        attack_message += f"\n恭喜！你升级了！当前等级: {attacker.level}"
    
    return {
        "type": "combat",
        "message": attack_message,
        "data": {
            "attacker": attacker.name,
            "defender": "测试靶子",
            "damage": damage,
            "defender_hp": dummy_hp - damage,
            "defender_max_hp": dummy_max_hp,
            "exp_gained": exp_gain,
            "level_up": level_up,
            "is_training_dummy": True
        }
    }


def attack_character(db: Session, attacker: Character, defender_name: str) -> dict:
    """攻击目标"""
    # 检查是否在同一房间
    if attacker.room_id != None:
        from game.world import get_room_by_id
        room = get_room_by_id(db, attacker.room_id)
        if not room:
            return {
                "type": "error",
                "message": "无法获取房间信息"
            }
        
        # 检查是否是训练场测试靶子
        if room.id == 4 and defender_name.lower() in ["测试靶子", "靶子", "dummy", "target"]:
            return attack_training_dummy(db, attacker)
        
        # 获取房间内的其他角色
        online_players = manager.get_online_characters_in_room(room.id, db)
        defender_info = None
        for p in online_players:
            if p["name"].lower() == defender_name.lower() and p["id"] != attacker.id:
                defender_info = p
                break
        
        # 如果没找到其他玩家，检查是否攻击自己
        if not defender_info:
            # 检查是否攻击自己
            if attacker.name.lower() == defender_name.lower():
                return {
                    "type": "error",
                    "message": "你不能攻击自己！"
                }
            
            # 检查是否是训练场测试靶子（如果名字不完全匹配）
            if room.id == 4:
                return {
                    "type": "error",
                    "message": f"找不到目标 '{defender_name}'。在训练场，你可以攻击 '测试靶子' 来练习。"
                }
            
            return {
                "type": "error",
                "message": f"找不到目标 '{defender_name}' 或目标不在同一房间"
            }
        
        defender = db.query(Character).filter(Character.id == defender_info["id"]).first()
    else:
        defender = db.query(Character).filter(Character.name.ilike(f"%{defender_name}%")).first()
    
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
    
    # 检查目标是否在线（对于玩家角色）
    if defender.id not in manager.character_to_user:
        return {
            "type": "error",
            "message": "目标不在线"
        }
    
    # 计算伤害
    damage = calculate_damage(attacker, defender)
    
    # 应用伤害
    defender.hp = max(0, defender.hp - damage)
    attacker_hp_after = attacker.hp
    defender_hp_after = defender.hp
    
    # 记录战斗日志
    combat_log = CombatLog(
        attacker_id=attacker.id,
        defender_id=defender.id,
        damage=damage,
        attacker_hp_after=attacker_hp_after,
        defender_hp_after=defender_hp_after
    )
    db.add(combat_log)
    
    # 如果目标死亡，给予经验值
    if defender.hp <= 0:
        exp_gain = defender.level * 20
        attacker.exp += exp_gain
        level_up = check_level_up(db, attacker)
        
        db.commit()
        
        # 通知攻击者
        attack_message = f"你击败了 {defender.name}！获得 {exp_gain} 经验值。"
        if level_up:
            attack_message += f"\n恭喜！你升级了！当前等级: {attacker.level}"
        
        # 通知防御者
        defend_message = f"{attacker.name} 击败了你！你失去了 {damage} 生命值。"
        if defender.hp <= 0:
            defend_message += "\n你被击败了！"
        
        return {
            "type": "combat",
            "message": attack_message,
            "data": {
                "attacker": attacker.name,
                "defender": defender.name,
                "damage": damage,
                "defender_hp": defender_hp_after,
                "exp_gained": exp_gain,
                "level_up": level_up
            },
            "defender_message": defend_message,
            "defender_id": defender.id
        }
    else:
        db.commit()
        
        attack_message = f"你对 {defender.name} 造成了 {damage} 点伤害！({defender.name} 剩余生命值: {defender_hp_after}/{defender.max_hp})"
        defend_message = f"{attacker.name} 对你造成了 {damage} 点伤害！(剩余生命值: {defender_hp_after}/{defender.max_hp})"
        
        return {
            "type": "combat",
            "message": attack_message,
            "data": {
                "attacker": attacker.name,
                "defender": defender.name,
                "damage": damage,
                "defender_hp": defender_hp_after
            },
            "defender_message": defend_message,
            "defender_id": defender.id
        }


def check_level_up(db: Session, character: Character) -> bool:
    """检查并处理升级"""
    exp_needed = character.level * 100
    
    if character.exp >= exp_needed:
        character.level += 1
        character.max_hp += 20
        character.hp = character.max_hp  # 升级时恢复满血
        character.max_mp += 10
        character.mp = character.max_mp  # 升级时恢复满魔
        character.attack += 2
        character.defense += 1
        db.commit()
        return True
    
    return False


def heal_character(character: Character, amount: int) -> dict:
    """治疗角色"""
    old_hp = character.hp
    character.hp = min(character.max_hp, character.hp + amount)
    healed = character.hp - old_hp
    
    return {
        "type": "success",
        "message": f"你恢复了 {healed} 点生命值！(当前: {character.hp}/{character.max_hp})",
        "data": {
            "healed": healed,
            "hp": character.hp,
            "max_hp": character.max_hp
        }
    }

