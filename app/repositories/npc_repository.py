"""NPC Repository"""
from typing import Optional, List
from sqlalchemy.orm import Session
from ..models import NPC
from .base_repository import BaseRepository


class NPCRepository(BaseRepository[NPC]):
    """NPC数据访问层"""
    
    def __init__(self, db: Session):
        super().__init__(db, NPC)
    
    def get_by_name(self, name: str) -> Optional[NPC]:
        """根据名称获取NPC"""
        return self.db.query(NPC).filter(NPC.name == name).first()
    
    def get_by_type(self, npc_type: str) -> List[NPC]:
        """根据类型获取NPC列表"""
        return self.db.query(NPC).filter(NPC.type == npc_type).all()
    
    def get_by_room(self, room_id: int) -> List[NPC]:
        """获取房间内的NPC"""
        return self.db.query(NPC).filter(NPC.room_id == room_id).all()
    
    def get_training_dummy_in_room(self, room_id: int) -> Optional[NPC]:
        """获取房间内的训练靶子"""
        return self.db.query(NPC).filter(
            NPC.room_id == room_id,
            NPC.type == "training_dummy"
        ).first()
