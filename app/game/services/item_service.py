"""物品服务 - 业务逻辑层"""
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from ...models import Character
from ...repositories.item_repository import ItemRepository
from ...repositories.character_repository import CharacterRepository


class ItemService:
    """物品服务 - 处理物品和装备相关的业务逻辑"""
    
    def __init__(self, db: Session):
        self.db = db
        self.item_repo = ItemRepository(db)
        self.character_repo = CharacterRepository(db)
    
    def get_character_inventory(self, character: Character) -> List[Dict]:
        """获取角色物品栏"""
        inventory_items = self.item_repo.get_character_inventory(character.id)
        result = []
        
        for inv_item in inventory_items:
            result.append({
                "id": inv_item.item_id,
                "name": inv_item.item.name,
                "description": inv_item.item.description,
                "type": inv_item.item.type,
                "slot": inv_item.item.slot,
                "quantity": inv_item.quantity,
                "stats": inv_item.item.stats
            })
        
        return result
    
    def add_item_to_inventory(self, character: Character, item_id: int, quantity: int = 1) -> bool:
        """添加物品到物品栏"""
        try:
            self.item_repo.add_to_inventory(character.id, item_id, quantity)
            return True
        except Exception:
            return False
    
    def remove_item_from_inventory(self, character: Character, item_id: int, quantity: int = 1) -> bool:
        """从物品栏移除物品"""
        return self.item_repo.remove_from_inventory(character.id, item_id, quantity)
    
    def equip_item(self, character: Character, item_name: str) -> Dict:
        """装备物品"""
        # 查找物品栏中的物品
        inventory_items = self.item_repo.get_character_inventory(character.id)
        target_item = None
        
        for inv_item in inventory_items:
            if inv_item.item.name.lower() == item_name.lower():
                target_item = inv_item.item
                break
        
        if not target_item:
            return {
                "type": "error",
                "message": f"物品栏中没有 '{item_name}'"
            }
        
        if target_item.type != "weapon" and target_item.type != "armor":
            return {
                "type": "error",
                "message": f"'{target_item.name}' 不是可装备的物品"
            }
        
        if not target_item.slot:
            return {
                "type": "error",
                "message": f"'{target_item.name}' 没有装备槽位"
            }
        
        # 检查该槽位是否已有装备
        existing_equipment = self.item_repo.get_equipment_by_slot(character.id, target_item.slot)
        
        # 如果有旧装备，先卸下
        if existing_equipment:
            old_item = existing_equipment.item
            # 移除旧装备的属性加成
            self._apply_item_stats(character, old_item, remove=True)
            # 将旧装备放回物品栏
            self.item_repo.add_to_inventory(character.id, old_item.id, 1)
            self.item_repo.unequip_item(character.id, target_item.slot)
        
        # 装备新物品
        self.item_repo.equip_item(character.id, target_item.slot, target_item.id)
        
        # 应用新装备的属性加成
        self._apply_item_stats(character, target_item, remove=False)
        
        # 从物品栏移除
        self.item_repo.remove_from_inventory(character.id, target_item.id, 1)
        
        self.db.commit()
        
        # 通知状态变化
        from .status_notifier import CharacterStatusNotifier
        status_notifier = CharacterStatusNotifier(self.db)
        status_notifier.notify_status_change_sync(character, "装备状态更新")
        
        return {
            "type": "success",
            "message": f"你装备了 {target_item.name}",
            "data": {
                "item": target_item.name,
                "slot": target_item.slot
            }
        }
    
    def unequip_item(self, character: Character, slot: str) -> Dict:
        """卸下装备"""
        equipment = self.item_repo.get_equipment_by_slot(character.id, slot)
        
        if not equipment:
            return {
                "type": "error",
                "message": f"你没有装备 {slot} 槽位的物品"
            }
        
        item = equipment.item
        
        # 移除属性加成
        self._apply_item_stats(character, item, remove=True)
        
        # 放回物品栏
        self.item_repo.add_to_inventory(character.id, item.id, 1)
        
        # 删除装备记录
        self.item_repo.unequip_item(character.id, slot)
        self.db.commit()
        
        # 通知状态变化
        from .status_notifier import CharacterStatusNotifier
        status_notifier = CharacterStatusNotifier(self.db)
        status_notifier.notify_status_change_sync(character, "卸下装备状态更新")
        
        return {
            "type": "success",
            "message": f"你卸下了 {item.name}",
            "data": {
                "item": item.name,
                "slot": slot
            }
        }
    
    def use_item(self, character: Character, item_name: str) -> Dict:
        """使用物品"""
        # 查找物品栏中的物品
        inventory_items = self.item_repo.get_character_inventory(character.id)
        target_item = None
        
        for inv_item in inventory_items:
            if inv_item.item.name.lower() == item_name.lower():
                target_item = inv_item.item
                break
        
        if not target_item:
            return {
                "type": "error",
                "message": f"物品栏中没有 '{item_name}'"
            }
        
        if target_item.type != "consumable":
            return {
                "type": "error",
                "message": f"'{target_item.name}' 不是消耗品"
            }
        
        # 应用物品效果
        message_parts = []
        
        if target_item.stats:
            if "hp" in target_item.stats:
                old_hp = character.hp
                character.hp = min(character.max_hp, character.hp + target_item.stats["hp"])
                healed = character.hp - old_hp
                if healed > 0:
                    message_parts.append(f"恢复了 {healed} 点生命值")
            
            if "mp" in target_item.stats:
                old_mp = character.mp
                character.mp = min(character.max_mp, character.mp + target_item.stats["mp"])
                restored = character.mp - old_mp
                if restored > 0:
                    message_parts.append(f"恢复了 {restored} 点魔法值")
        
        message = f"你使用了 {target_item.name}，" + "，".join(message_parts) + "！" if message_parts else f"你使用了 {target_item.name}，但没有效果。"
        
        # 移除物品
        self.item_repo.remove_from_inventory(character.id, target_item.id, 1)
        self.db.commit()
        
        # 通知状态变化
        from .status_notifier import CharacterStatusNotifier
        status_notifier = CharacterStatusNotifier(self.db)
        status_notifier.notify_status_change_sync(character, "使用物品状态更新")
        
        return {
            "type": "success",
            "message": message,
            "data": {
                "item": target_item.name,
                "hp": character.hp,
                "max_hp": character.max_hp,
                "mp": character.mp,
                "max_mp": character.max_mp
            }
        }
    
    def get_character_equipment(self, character: Character) -> Dict:
        """获取角色当前装备"""
        equipment_items = self.item_repo.get_character_equipment(character.id)
        equipment_dict = {}
        
        for eq in equipment_items:
            equipment_dict[eq.slot] = {
                "id": eq.item.id,
                "name": eq.item.name,
                "description": eq.item.description,
                "stats": eq.item.stats
            }
        
        return equipment_dict
    
    def _apply_item_stats(self, character: Character, item, remove: bool = False):
        """应用或移除物品属性加成"""
        if not item.stats:
            return
        
        multiplier = -1 if remove else 1
        
        if "attack" in item.stats:
            character.attack += item.stats["attack"] * multiplier
        if "defense" in item.stats:
            character.defense += item.stats["defense"] * multiplier
        if "hp" in item.stats:
            character.max_hp += item.stats["hp"] * multiplier
            if not remove:
                character.hp += item.stats["hp"]  # 装备时增加当前HP
            else:
                character.hp = min(character.hp, character.max_hp)  # 卸下时确保HP不超过最大值
        if "mp" in item.stats:
            character.max_mp += item.stats["mp"] * multiplier
            if not remove:
                character.mp += item.stats["mp"]  # 装备时增加当前MP
            else:
                character.mp = min(character.mp, character.max_mp)  # 卸下时确保MP不超过最大值
