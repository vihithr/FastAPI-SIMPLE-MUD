"""物品和装备系统"""
from sqlalchemy.orm import Session
from ..models import Character, Item, Inventory, Equipment
from typing import List, Optional


def get_character_inventory(db: Session, character: Character) -> List[dict]:
    """获取角色物品栏"""
    inventory_items = db.query(Inventory).filter(Inventory.character_id == character.id).all()
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


def add_item_to_inventory(db: Session, character: Character, item_id: int, quantity: int = 1) -> bool:
    """添加物品到物品栏"""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        return False
    
    # 检查是否已有该物品
    existing = db.query(Inventory).filter(
        Inventory.character_id == character.id,
        Inventory.item_id == item_id
    ).first()
    
    if existing:
        existing.quantity += quantity
    else:
        new_inventory = Inventory(
            character_id=character.id,
            item_id=item_id,
            quantity=quantity
        )
        db.add(new_inventory)
    
    db.commit()
    return True


def remove_item_from_inventory(db: Session, character: Character, item_id: int, quantity: int = 1) -> bool:
    """从物品栏移除物品"""
    inventory_item = db.query(Inventory).filter(
        Inventory.character_id == character.id,
        Inventory.item_id == item_id
    ).first()
    
    if not inventory_item or inventory_item.quantity < quantity:
        return False
    
    inventory_item.quantity -= quantity
    if inventory_item.quantity <= 0:
        db.delete(inventory_item)
    
    db.commit()
    return True


def equip_item(db: Session, character: Character, item_name: str) -> dict:
    """装备物品"""
    # 查找物品栏中的物品
    inventory_items = db.query(Inventory).filter(Inventory.character_id == character.id).all()
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
    existing_equipment = db.query(Equipment).filter(
        Equipment.character_id == character.id,
        Equipment.slot == target_item.slot
    ).first()
    
    # 如果有旧装备，先卸下
    if existing_equipment:
        old_item = existing_equipment.item
        # 移除旧装备的属性加成
        if old_item.stats:
            if "attack" in old_item.stats:
                character.attack -= old_item.stats["attack"]
            if "defense" in old_item.stats:
                character.defense -= old_item.stats["defense"]
            if "hp" in old_item.stats:
                character.max_hp -= old_item.stats["hp"]
            if "mp" in old_item.stats:
                character.max_mp -= old_item.stats["mp"]
        
        # 将旧装备放回物品栏
        add_item_to_inventory(db, character, old_item.id, 1)
        db.delete(existing_equipment)
    
    # 装备新物品
    new_equipment = Equipment(
        character_id=character.id,
        slot=target_item.slot,
        item_id=target_item.id
    )
    db.add(new_equipment)
    
    # 应用新装备的属性加成
    if target_item.stats:
        if "attack" in target_item.stats:
            character.attack += target_item.stats["attack"]
        if "defense" in target_item.stats:
            character.defense += target_item.stats["defense"]
        if "hp" in target_item.stats:
            character.max_hp += target_item.stats["hp"]
            character.hp += target_item.stats["hp"]  # 同时增加当前HP
        if "mp" in target_item.stats:
            character.max_mp += target_item.stats["mp"]
            character.mp += target_item.stats["mp"]  # 同时增加当前MP
    
    # 从物品栏移除
    remove_item_from_inventory(db, character, target_item.id, 1)
    
    db.commit()
    
    return {
        "type": "success",
        "message": f"你装备了 {target_item.name}",
        "data": {
            "item": target_item.name,
            "slot": target_item.slot
        }
    }


def unequip_item(db: Session, character: Character, slot: str) -> dict:
    """卸下装备"""
    equipment = db.query(Equipment).filter(
        Equipment.character_id == character.id,
        Equipment.slot == slot
    ).first()
    
    if not equipment:
        return {
            "type": "error",
            "message": f"你没有装备 {slot} 槽位的物品"
        }
    
    item = equipment.item
    
    # 移除属性加成
    if item.stats:
        if "attack" in item.stats:
            character.attack -= item.stats["attack"]
        if "defense" in item.stats:
            character.defense -= item.stats["defense"]
        if "hp" in item.stats:
            character.max_hp -= item.stats["hp"]
            character.hp = min(character.hp, character.max_hp)  # 确保HP不超过最大值
        if "mp" in item.stats:
            character.max_mp -= item.stats["mp"]
            character.mp = min(character.mp, character.max_mp)  # 确保MP不超过最大值
    
    # 放回物品栏
    add_item_to_inventory(db, character, item.id, 1)
    
    # 删除装备记录
    db.delete(equipment)
    db.commit()
    
    return {
        "type": "success",
        "message": f"你卸下了 {item.name}",
        "data": {
            "item": item.name,
            "slot": slot
        }
    }


def use_item(db: Session, character: Character, item_name: str) -> dict:
    """使用物品"""
    # 查找物品栏中的物品
    inventory_items = db.query(Inventory).filter(Inventory.character_id == character.id).all()
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
    if target_item.stats:
        message_parts = []
        
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
        
        message = f"你使用了 {target_item.name}，" + "，".join(message_parts) + "！"
    else:
        message = f"你使用了 {target_item.name}，但没有效果。"
    
    # 移除物品
    remove_item_from_inventory(db, character, target_item.id, 1)
    db.commit()
    
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


def get_character_equipment(db: Session, character: Character) -> dict:
    """获取角色当前装备"""
    equipment_items = db.query(Equipment).filter(Equipment.character_id == character.id).all()
    equipment_dict = {}
    
    for eq in equipment_items:
        equipment_dict[eq.slot] = {
            "id": eq.item.id,
            "name": eq.item.name,
            "description": eq.item.description,
            "stats": eq.item.stats
        }
    
    return equipment_dict

