"""卸下装备命令"""
from typing import Dict
from sqlalchemy.orm import Session
from ...models import Character
from .base_command import Command
from ..services.item_service import ItemService


class UnequipCommand(Command):
    """卸下装备命令"""
    
    def __init__(self):
        super().__init__("unequip", ["remove"])
    
    async def execute(
        self,
        db: Session,
        character: Character,
        args: list,
        **kwargs
    ) -> Dict:
        """执行卸下装备命令"""
        if not args:
            return {
                "type": "error",
                "message": "请指定要卸下的装备槽位。用法: unequip <槽位>"
            }
        
        slot = args[0].lower()
        item_service = ItemService(db)
        return item_service.unequip_item(character, slot)
