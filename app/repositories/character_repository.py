"""角色Repository"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..models import Character
from .base_repository import BaseRepository


class CharacterRepository(BaseRepository[Character]):
    """角色数据访问层"""
    
    def __init__(self, db: Session):
        super().__init__(db, Character)
    
    def get_by_user_id(self, user_id: int) -> Optional[Character]:
        """根据用户ID获取角色"""
        return self.db.query(Character).filter(Character.user_id == user_id).first()
    
    def get_by_name(self, name: str) -> Optional[Character]:
        """根据名称获取角色（精确匹配）"""
        return self.db.query(Character).filter(Character.name == name).first()
    
    def search_by_name(self, name: str) -> List[Character]:
        """根据名称搜索角色（模糊匹配）"""
        return self.db.query(Character).filter(
            Character.name.ilike(f"%{name}%")
        ).all()
    
    def get_characters_in_room(self, room_id: int) -> List[Character]:
        """获取房间内的所有角色"""
        return self.db.query(Character).filter(Character.room_id == room_id).all()
    
    def update_room(self, character_id: int, room_id: int) -> Optional[Character]:
        """更新角色所在房间"""
        character = self.get_by_id(character_id)
        if character:
            character.room_id = room_id
            return self.update(character)
        return None
    
    def update_hp(self, character_id: int, hp: int) -> Optional[Character]:
        """更新角色生命值"""
        character = self.get_by_id(character_id)
        if character:
            character.hp = max(0, min(hp, character.max_hp))
            return self.update(character)
        return None
    
    def add_exp(self, character_id: int, exp: int) -> Optional[Character]:
        """增加角色经验值"""
        character = self.get_by_id(character_id)
        if character:
            character.exp += exp
            return self.update(character)
        return None
