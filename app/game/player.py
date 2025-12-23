"""玩家系统"""
from sqlalchemy.orm import Session
from ..models import Character, Room
from .world import get_room_by_id, get_room_exits
from ..websocket.manager import manager


def move_character(db: Session, character: Character, direction: str) -> dict:
    """移动角色"""
    direction_map = {
        "north": "north",
        "n": "north",
        "south": "south",
        "s": "south",
        "east": "east",
        "e": "east",
        "west": "west",
        "w": "west"
    }
    
    direction = direction.lower()
    if direction not in direction_map:
        return {
            "type": "error",
            "message": f"无效的方向: {direction}。可用方向: north(n), south(s), east(e), west(w)"
        }
    
    normalized_direction = direction_map[direction]
    current_room = get_room_by_id(db, character.room_id)
    
    if not current_room or not current_room.exits:
        return {
            "type": "error",
            "message": "无法获取当前房间信息"
        }
    
    if normalized_direction not in current_room.exits:
        return {
            "type": "error",
            "message": f"这个方向没有出口"
        }
    
    new_room_id = current_room.exits[normalized_direction]
    new_room = get_room_by_id(db, new_room_id)
    
    if not new_room:
        return {
            "type": "error",
            "message": "目标房间不存在"
        }
    
    # 更新角色位置
    old_room_id = character.room_id
    character.room_id = new_room_id
    db.commit()
    
    # 更新连接管理器中的房间信息
    manager.update_character_room(character.id, old_room_id, new_room_id)
    
    return {
        "type": "success",
        "message": f"你移动到了 {new_room.name}",
        "data": {
            "room": {
                "id": new_room.id,
                "name": new_room.name,
                "description": new_room.description,
                "exits": get_room_exits(new_room)
            }
        }
    }


def look_room(db: Session, character: Character) -> dict:
    """查看当前房间"""
    room = get_room_by_id(db, character.room_id)
    if not room:
        return {
            "type": "error",
            "message": "无法获取房间信息"
        }
    
    # 获取房间内其他玩家
    online_players = manager.get_online_characters_in_room(room.id, db)
    other_players = [p for p in online_players if p["id"] != character.id]
    
    exits_info = get_room_exits(room)
    exits_text = ", ".join(exits_info.keys()) if exits_info else "无"
    
    message = f"{room.name}\n\n{room.description}\n\n"
    
    # 如果是训练场，显示测试靶子信息
    if room.id == 4:
        message += "这里有一个测试靶子，你可以使用 'attack 测试靶子' 来练习战斗。\n\n"
    
    if other_players:
        player_names = ", ".join([p["name"] for p in other_players])
        message += f"房间内的其他玩家: {player_names}\n\n"
    message += f"出口: {exits_text}"
    
    from .commands import get_available_commands

    return {
        "type": "room",
        "message": message,
        "data": {
            "room": {
                "id": room.id,
                "name": room.name,
                "description": room.description,
                "exits": exits_info
            },
            "players": other_players,
            "available_commands": get_available_commands(db, character),
        }
    }


def get_character_stats(character: Character) -> dict:
    """获取角色属性"""
    exp_to_next_level = character.level * 100 - character.exp
    
    message = f"""
角色: {character.name}
等级: {character.level}
生命值: {character.hp}/{character.max_hp}
魔法值: {character.mp}/{character.max_mp}
攻击力: {character.attack}
防御力: {character.defense}
经验值: {character.exp} (距离下一级还需 {exp_to_next_level} 经验)
"""
    
    return {
        "type": "info",
        "message": message.strip(),
        "data": {
            "name": character.name,
            "level": character.level,
            "hp": character.hp,
            "max_hp": character.max_hp,
            "mp": character.mp,
            "max_mp": character.max_mp,
            "attack": character.attack,
            "defense": character.defense,
            "exp": character.exp
        }
    }

