"""物品栏命令"""
from typing import Dict
from sqlalchemy.orm import Session
from ...models import Character
from .base_command import Command
from ..services.item_service import ItemService


class InventoryCommand(Command):
    """查看物品栏命令"""
    
    def __init__(self):
        super().__init__("inventory", ["inv", "bag", "items"])
    
    async def execute(
        self,
        db: Session,
        character: Character,
        args: list,
        **kwargs
    ) -> Dict:
        """执行查看物品栏命令"""
        item_service = ItemService(db)
        inventory = item_service.get_character_inventory(character)
        
        if not inventory:
            return {
                "type": "info",
                "message": "你的物品栏是空的",
                "data": {"inventory": []}
            }
        
        items_text = "\n".join([
            f"- {item['name']} x{item['quantity']} ({item['type']})"
            for item in inventory
        ])
        
        return {
            "type": "info",
            "message": f"物品栏:\n{items_text}",
            "data": {"inventory": inventory}
        }
