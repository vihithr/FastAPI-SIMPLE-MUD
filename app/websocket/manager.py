"""WebSocket连接管理器"""
from typing import Dict, Set
from fastapi import WebSocket
from sqlalchemy.orm import Session
from ..models import Character, Room


class ConnectionManager:
    """管理WebSocket连接"""
    
    def __init__(self):
        # user_id -> websocket
        self.active_connections: Dict[int, WebSocket] = {}
        # character_id -> user_id
        self.character_to_user: Dict[int, int] = {}
        # room_id -> set of character_ids
        self.room_connections: Dict[int, Set[int]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int, character_id: int, room_id: int):
        """建立连接"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.character_to_user[character_id] = user_id
        
        # 添加到房间连接集合
        if room_id not in self.room_connections:
            self.room_connections[room_id] = set()
        self.room_connections[room_id].add(character_id)
    
    def disconnect(self, user_id: int, character_id: int, room_id: int):
        """断开连接"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        if character_id in self.character_to_user:
            del self.character_to_user[character_id]
        
        # 从房间连接集合中移除
        if room_id in self.room_connections:
            self.room_connections[room_id].discard(character_id)
            if len(self.room_connections[room_id]) == 0:
                del self.room_connections[room_id]
    
    async def send_personal_message(self, message: dict, user_id: int):
        """发送个人消息"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                print(f"Error sending message to user {user_id}: {e}")
    
    async def broadcast_to_room(self, message: dict, room_id: int, exclude_character_id: int = None, db: Session = None):
        """向房间内所有玩家广播消息"""
        if room_id not in self.room_connections:
            return
        
        for character_id in self.room_connections[room_id]:
            if exclude_character_id and character_id == exclude_character_id:
                continue
            
            if character_id in self.character_to_user:
                user_id = self.character_to_user[character_id]
                await self.send_personal_message(message, user_id)
    
    def update_character_room(self, character_id: int, old_room_id: int, new_room_id: int):
        """更新角色所在房间"""
        # 从旧房间移除
        if old_room_id in self.room_connections:
            self.room_connections[old_room_id].discard(character_id)
            if len(self.room_connections[old_room_id]) == 0:
                del self.room_connections[old_room_id]
        
        # 添加到新房间
        if new_room_id not in self.room_connections:
            self.room_connections[new_room_id] = set()
        self.room_connections[new_room_id].add(character_id)
    
    def get_online_characters_in_room(self, room_id: int, db: Session) -> list:
        """获取房间内在线的角色列表"""
        if room_id not in self.room_connections:
            return []
        
        character_ids = list(self.room_connections[room_id])
        characters = db.query(Character).filter(Character.id.in_(character_ids)).all()
        return [{"id": c.id, "name": c.name, "level": c.level} for c in characters]


# 全局连接管理器实例
manager = ConnectionManager()

