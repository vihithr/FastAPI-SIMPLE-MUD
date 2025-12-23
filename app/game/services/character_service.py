"""角色服务 - 业务逻辑层"""
from typing import Dict, Optional
from sqlalchemy.orm import Session
from ...models import Character
from ...repositories.character_repository import CharacterRepository
from ...repositories.room_repository import RoomRepository


class CharacterService:
    """角色服务 - 处理角色相关的业务逻辑"""
    
    def __init__(self, db: Session):
        self.db = db
        self.character_repo = CharacterRepository(db)
        self.room_repo = RoomRepository(db)
    
    def move_character(self, character: Character, direction: str) -> Dict:
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
        current_room = self.room_repo.get_by_id(character.room_id)
        
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
        new_room = self.room_repo.get_by_id(new_room_id)
        
        if not new_room:
            return {
                "type": "error",
                "message": "目标房间不存在"
            }
        
        # 更新角色位置
        old_room_id = character.room_id
        updated_character = self.character_repo.update_room(character.id, new_room_id)
        
        if not updated_character:
            return {
                "type": "error",
                "message": "更新角色位置失败"
            }
        
        # 更新连接管理器中的房间信息
        from ...websocket.manager import manager
        manager.update_character_room(character.id, old_room_id, new_room_id)
        
        # 获取房间出口信息
        exits_info = self._get_room_exits(new_room)
        
        return {
            "type": "success",
            "message": f"你移动到了 {new_room.name}",
            "data": {
                "room": {
                    "id": new_room.id,
                    "name": new_room.name,
                    "description": new_room.description,
                    "exits": exits_info
                }
            }
        }
    
    def look_room(self, character: Character) -> Dict:
        """查看当前房间"""
        room = self.room_repo.get_by_id(character.room_id)
        if not room:
            return {
                "type": "error",
                "message": "无法获取房间信息"
            }
        
        # 获取房间内其他玩家
        from ...websocket.manager import manager
        online_players = manager.get_online_characters_in_room(room.id, self.db)
        other_players = [p for p in online_players if p["id"] != character.id]
        
        exits_info = self._get_room_exits(room)
        exits_text = ", ".join(exits_info.keys()) if exits_info else "无"
        
        message = f"{room.name}\n\n{room.description}\n\n"
        
        # 检查是否有训练靶子
        from ...repositories.npc_repository import NPCRepository
        npc_repo = NPCRepository(self.db)
        training_dummy = npc_repo.get_training_dummy_in_room(room.id)
        if training_dummy:
            message += f"这里有一个{training_dummy.name}，你可以使用 'attack {training_dummy.name}' 来练习战斗。\n\n"
        
        if other_players:
            player_names = ", ".join([p["name"] for p in other_players])
            message += f"房间内的其他玩家: {player_names}\n\n"
        message += f"出口: {exits_text}"
        
        from .room_service import RoomService
        room_service = RoomService(self.db)
        available_commands = room_service.get_available_commands(character)
        
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
                "available_commands": available_commands,
            }
        }
    
    def get_character_stats(self, character: Character) -> Dict:
        """获取角色属性"""
        from .config_service import ConfigService
        config_service = ConfigService(self.db)
        leveling_config = config_service.get_leveling_config()
        exp_per_level = leveling_config.get("exp_per_level", 100)
        exp_to_next_level = character.level * exp_per_level - character.exp
        
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
    
    def _get_room_exits(self, room) -> Dict[str, int]:
        """获取房间出口方向名称"""
        if not room or not room.exits:
            return {}
        
        exit_names = {}
        direction_map = {
            "north": "北",
            "south": "南",
            "east": "东",
            "west": "西"
        }
        
        for direction, target_room_id in room.exits.items():
            exit_names[direction_map.get(direction, direction)] = target_room_id
        
        return exit_names
