"""物品Repository"""
from typing import Optional, List
from sqlalchemy.orm import Session
from ..models import Item, Inventory, Equipment
from .base_repository import BaseRepository


class ItemRepository(BaseRepository[Item]):
    """物品数据访问层"""
    
    def __init__(self, db: Session):
        super().__init__(db, Item)
    
    def get_by_name(self, name: str) -> Optional[Item]:
        """根据名称获取物品（精确匹配）"""
        return self.db.query(Item).filter(Item.name == name).first()
    
    def search_by_name(self, name: str) -> Optional[Item]:
        """根据名称搜索物品（模糊匹配）"""
        return self.db.query(Item).filter(Item.name.ilike(f"%{name}%")).first()
    
    def get_by_type(self, item_type: str) -> List[Item]:
        """根据类型获取物品列表"""
        return self.db.query(Item).filter(Item.type == item_type).all()
    
    def get_character_inventory(self, character_id: int) -> List[Inventory]:
        """获取角色的物品栏"""
        return self.db.query(Inventory).filter(Inventory.character_id == character_id).all()
    
    def get_inventory_item(self, character_id: int, item_id: int) -> Optional[Inventory]:
        """获取角色物品栏中的特定物品"""
        return self.db.query(Inventory).filter(
            Inventory.character_id == character_id,
            Inventory.item_id == item_id
        ).first()
    
    def add_to_inventory(self, character_id: int, item_id: int, quantity: int = 1) -> Inventory:
        """添加物品到物品栏"""
        existing = self.get_inventory_item(character_id, item_id)
        if existing:
            existing.quantity += quantity
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            new_inventory = Inventory(
                character_id=character_id,
                item_id=item_id,
                quantity=quantity
            )
            self.db.add(new_inventory)
            self.db.commit()
            self.db.refresh(new_inventory)
            return new_inventory
    
    def remove_from_inventory(self, character_id: int, item_id: int, quantity: int = 1) -> bool:
        """从物品栏移除物品"""
        inventory_item = self.get_inventory_item(character_id, item_id)
        if not inventory_item or inventory_item.quantity < quantity:
            return False
        
        inventory_item.quantity -= quantity
        if inventory_item.quantity <= 0:
            self.db.delete(inventory_item)
        self.db.commit()
        return True
    
    def get_character_equipment(self, character_id: int) -> List[Equipment]:
        """获取角色的装备"""
        return self.db.query(Equipment).filter(Equipment.character_id == character_id).all()
    
    def get_equipment_by_slot(self, character_id: int, slot: str) -> Optional[Equipment]:
        """根据槽位获取装备"""
        return self.db.query(Equipment).filter(
            Equipment.character_id == character_id,
            Equipment.slot == slot
        ).first()
    
    def equip_item(self, character_id: int, slot: str, item_id: int) -> Equipment:
        """装备物品"""
        # 先检查是否已有装备
        existing = self.get_equipment_by_slot(character_id, slot)
        if existing:
            self.db.delete(existing)
        
        new_equipment = Equipment(
            character_id=character_id,
            slot=slot,
            item_id=item_id
        )
        self.db.add(new_equipment)
        self.db.commit()
        self.db.refresh(new_equipment)
        return new_equipment
    
    def unequip_item(self, character_id: int, slot: str) -> bool:
        """卸下装备"""
        equipment = self.get_equipment_by_slot(character_id, slot)
        if equipment:
            self.db.delete(equipment)
            self.db.commit()
            return True
        return False
