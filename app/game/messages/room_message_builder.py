"""房间消息构建器"""
from typing import Dict, Any, List
from .message_builder import MessageBuilder


class RoomMessageBuilder(MessageBuilder):
    """房间消息构建器"""
    
    @staticmethod
    def build_room_description(
        room_name: str,
        room_description: str,
        exits: Dict[str, int],
        other_players: List[Dict] = None,
        npcs: List[Dict] = None
    ) -> str:
        """构建房间描述消息"""
        message = f"{room_name}\n\n{room_description}\n\n"
        
        # 添加NPC信息
        if npcs:
            for npc in npcs:
                npc_type = npc.get("type", "")
                if npc_type == "training_dummy":
                    message += f"这里有一个{npc.get('name', '测试靶子')}，你可以使用 'attack {npc.get('name', '测试靶子')}' 来练习战斗。\n\n"
        
        # 添加其他玩家信息
        if other_players:
            player_names = ", ".join([p.get("name", "未知") for p in other_players])
            message += f"房间内的其他玩家: {player_names}\n\n"
        
        # 添加出口信息
        direction_map = {
            "north": "北",
            "south": "南",
            "east": "东",
            "west": "西"
        }
        exit_names = [direction_map.get(d, d) for d in exits.keys()]
        exits_text = ", ".join(exit_names) if exit_names else "无"
        message += f"出口: {exits_text}"
        
        return message
    
    def build(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """构建房间消息"""
        room = data.get("room", {})
        other_players = data.get("players", [])
        npcs = data.get("npcs", [])
        available_commands = data.get("available_commands", {})
        
        message = self.build_room_description(
            room.get("name", "未知房间"),
            room.get("description", ""),
            room.get("exits", {}),
            other_players,
            npcs
        )
        
        return self.create_message("room", message, {
            "room": room,
            "players": other_players,
            "available_commands": available_commands
        })
