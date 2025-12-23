"""战斗系统 - 无状态掷骰判定系统"""
import random
from typing import Dict, Tuple
from sqlalchemy.orm import Session
from ..models import Character, CombatLog
from ..websocket.manager import manager


def roll_dice(sides: int, count: int = 1) -> int:
    """掷骰子"""
    return sum(random.randint(1, sides) for _ in range(count))


def roll_to_hit(attacker_attack: int, defender_defense: int) -> Tuple[bool, int, bool]:
    """
    掷骰判定命中
    返回: (是否命中, 掷骰结果, 是否暴击)
    
    规则:
    - 基础命中: 1d20 + 攻击力修正
    - 命中判定: 掷骰结果 >= 防御力 + 10
    - 暴击: 自然20 (d20 = 20) 必定命中且伤害翻倍
    - 失误: 自然1 (d20 = 1) 必定未命中
    """
    d20_roll = roll_dice(20, 1)
    attack_modifier = attacker_attack // 2  # 攻击力的一半作为修正值
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


def roll_damage(attacker_attack: int, is_critical: bool = False) -> int:
    """
    掷骰计算伤害
    
    规则:
    - 基础伤害: 1d(攻击力) + 攻击力修正
    - 暴击伤害: 基础伤害 x 2
    - 最小伤害: 1
    """
    # 基础伤害骰: 1d(攻击力)，最小为1d4
    damage_die = max(4, attacker_attack)
    base_damage = roll_dice(damage_die, 1)
    
    # 攻击力修正 (攻击力的1/3)
    attack_modifier = max(1, attacker_attack // 3)
    
    total_damage = base_damage + attack_modifier
    
    # 暴击伤害翻倍
    if is_critical:
        total_damage *= 2
    
    return max(1, total_damage)


def apply_defense_reduction(damage: int, defender_defense: int) -> int:
    """
    应用防御减免
    
    规则:
    - 防御减免 = 防御力 / 2 (向下取整)
    - 最小伤害: 1
    """
    defense_reduction = defender_defense // 2
    final_damage = max(1, damage - defense_reduction)
    return final_damage


def resolve_attack(
    attacker_attack: int,
    defender_defense: int,
    defender_hp: int,
    defender_max_hp: int
) -> Dict:
    """
    解析一次攻击 (完全无状态)
    
    返回战斗结果字典，包含:
    - hit: 是否命中
    - critical: 是否暴击
    - damage: 造成的伤害
    - roll_result: 命中掷骰结果
    - defender_hp_after: 防御者剩余生命值
    """
    # 掷骰判定命中
    hit, roll_result, is_critical = roll_to_hit(attacker_attack, defender_defense)
    
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
    damage = roll_damage(attacker_attack, is_critical)
    
    # 应用防御减免
    final_damage = apply_defense_reduction(damage, defender_defense)
    
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


def attack_training_dummy(db: Session, attacker: Character) -> dict:
    """攻击训练场测试靶子 (使用掷骰系统)"""
    try:
        # 测试靶子属性：高血量，低防御，不会反击
        dummy_defense = 0
        dummy_max_hp = 1000
        dummy_hp = dummy_max_hp  # 测试靶子总是满血
        
        # 使用掷骰系统解析攻击
        combat_result = resolve_attack(
            attacker_attack=attacker.attack,
            defender_defense=dummy_defense,
            defender_hp=dummy_hp,
            defender_max_hp=dummy_max_hp
        )
        
        # 构建消息
        if combat_result["miss"]:
            attack_message = f"你攻击测试靶子，但未命中！(掷骰: {combat_result['roll_result']})"
            exp_gain = 1  # 未命中也给少量经验
        else:
            damage = combat_result["damage"]
            critical_text = " (暴击！)" if combat_result["critical"] else ""
            attack_message = f"你对测试靶子造成了 {damage} 点伤害{critical_text}！(掷骰: {combat_result['roll_result']}, 测试靶子剩余生命值: {combat_result['defender_hp_after']}/{dummy_max_hp})"
            exp_gain = 5  # 命中给更多经验
        
        # 给予经验值（训练奖励）
        attacker.exp += exp_gain
        
        # 检查升级（check_level_up 内部会处理提交）
        level_up = False
        try:
            level_up = check_level_up(db, attacker)
        except Exception as e:
            print(f"Error in check_level_up during training dummy attack: {e}")
            # 即使升级检查失败，也要提交经验值
            db.commit()
        
        # 如果升级了，check_level_up 已经提交了，否则需要提交经验值
        if not level_up:
            try:
                db.commit()
            except Exception as e:
                print(f"Error committing exp gain: {e}")
                db.rollback()
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
                "defender_hp": combat_result["defender_hp_after"],
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
        # 如果出错，回滚并返回错误
        try:
            db.rollback()
        except:
            pass
        print(f"Error in attack_training_dummy: {e}")
        import traceback
        traceback.print_exc()
        return {
            "type": "error",
            "message": f"攻击测试靶子时发生错误: {str(e)}"
        }


def attack_character(db: Session, attacker: Character, defender_name: str) -> dict:
    """攻击目标 (使用掷骰系统)"""
    # 检查是否在同一房间
    if attacker.room_id != None:
        from .world import get_room_by_id
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
    
    # 使用掷骰系统解析攻击 (完全无状态)
    combat_result = resolve_attack(
        attacker_attack=attacker.attack,
        defender_defense=defender.defense,
        defender_hp=defender.hp,
        defender_max_hp=defender.max_hp
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
    db.add(combat_log)
    
    # 构建消息
    if combat_result["miss"]:
        attack_message = f"你攻击 {defender.name}，但未命中！(掷骰: {combat_result['roll_result']})"
        defend_message = f"{attacker.name} 攻击你，但未命中！(掷骰: {combat_result['roll_result']})"
        exp_gain = 0
        level_up = False
    else:
        damage = combat_result["damage"]
        critical_text = " (暴击！)" if combat_result["critical"] else ""
        
        # 如果目标死亡，给予经验值
        if defender.hp <= 0:
            exp_gain = defender.level * 20
            attacker.exp += exp_gain
            level_up = check_level_up(db, attacker)
            
            attack_message = f"你击败了 {defender.name}！造成 {damage} 点伤害{critical_text}！(掷骰: {combat_result['roll_result']})\n获得 {exp_gain} 经验值。"
            if level_up:
                attack_message += f"\n恭喜！你升级了！当前等级: {attacker.level}"
            
            defend_message = f"{attacker.name} 击败了你！你失去了 {damage} 生命值{critical_text}。\n你被击败了！"
        else:
            attack_message = f"你对 {defender.name} 造成了 {damage} 点伤害{critical_text}！(掷骰: {combat_result['roll_result']}, {defender.name} 剩余生命值: {defender_hp_after}/{defender.max_hp})"
            defend_message = f"{attacker.name} 对你造成了 {damage} 点伤害{critical_text}！(掷骰: {combat_result['roll_result']}, 剩余生命值: {defender_hp_after}/{defender.max_hp})"
            exp_gain = 0
            level_up = False
    
    # 提交数据库更改
    db.commit()
    
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


def check_level_up(db: Session, character: Character) -> bool:
    """检查并处理升级"""
    try:
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
    except Exception as e:
        print(f"Error in check_level_up: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
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

