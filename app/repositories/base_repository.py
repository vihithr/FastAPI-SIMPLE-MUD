"""基础Repository接口"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """基础Repository抽象类"""
    
    def __init__(self, db: Session, model: type[T]):
        self.db = db
        self.model = model
    
    def get_by_id(self, id: int) -> Optional[T]:
        """根据ID获取实体"""
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """获取所有实体（分页）"""
        return self.db.query(self.model).offset(skip).limit(limit).all()
    
    def create(self, entity: T) -> T:
        """创建实体"""
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def update(self, entity: T) -> T:
        """更新实体"""
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def delete(self, entity: T) -> bool:
        """删除实体"""
        self.db.delete(entity)
        self.db.commit()
        return True
    
    def delete_by_id(self, id: int) -> bool:
        """根据ID删除实体"""
        entity = self.get_by_id(id)
        if entity:
            return self.delete(entity)
        return False
