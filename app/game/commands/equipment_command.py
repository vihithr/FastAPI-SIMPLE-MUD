"""装备查看命令"""
from typing import Dict
from sqlalchemy.orm import Session
from ...models import Character
from .base_command import Command
from ..services.item_service import ItemService


class EquipmentCommand(Command):
    """查看装备命令"""
    
    def __init__(self):
        super().__init__("equipment", ["equipments", "eq"])
    
    async def execute(
        self,
        db: Session,
        character: Character,
        args: list,
        **kwargs
    ) -> Dict:
        """执行查看装备命令"""
        item_service = ItemService(db)
        equipment = item_service.get_character_equipment(character)
        
        if not equipment:
            return {
                "type": "info",
                "message": "你没有装备任何物品",
                "data": {"equipment": {}}
            }
        
        eq_text = "\n".join([
            f"- {slot}: {item['name']}"
            for slot, item in equipment.items()
        ])
        
        return {
            "type": "info",
            "message": f"当前装备:\n{eq_text}",
            "data": {"equipment": equipment}
        }
