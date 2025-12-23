"""房间Repository"""
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from ..models import Room, Command, RoomCommand
from .base_repository import BaseRepository


class RoomRepository(BaseRepository[Room]):
    """房间数据访问层"""
    
    def __init__(self, db: Session):
        super().__init__(db, Room)
    
    def get_by_name(self, name: str) -> Optional[Room]:
        """根据名称获取房间"""
        return self.db.query(Room).filter(Room.name == name).first()
    
    def get_room_exits(self, room_id: int) -> Dict[str, int]:
        """获取房间出口"""
        room = self.get_by_id(room_id)
        if room and room.exits:
            return room.exits
        return {}
    
    def get_available_commands(self, room_id: int) -> List[Command]:
        """获取房间可用的命令"""
        return (
            self.db.query(Command)
            .join(RoomCommand, RoomCommand.command_id == Command.id)
            .filter(RoomCommand.room_id == room_id)
            .all()
        )
    
    def get_characters_in_room(self, room_id: int) -> List:
        """获取房间内的角色（返回基本信息）"""
        from ..models import Character
        characters = self.db.query(Character).filter(Character.room_id == room_id).all()
        return [{"id": c.id, "name": c.name, "level": c.level} for c in characters]
