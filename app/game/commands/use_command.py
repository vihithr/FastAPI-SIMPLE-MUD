"""使用物品命令"""
from typing import Dict
from sqlalchemy.orm import Session
from ...models import Character
from .base_command import Command
from ..services.item_service import ItemService


class UseCommand(Command):
    """使用物品命令"""
    
    def __init__(self):
        super().__init__("use", ["drink", "eat"])
    
    async def execute(
        self,
        db: Session,
        character: Character,
        args: list,
        **kwargs
    ) -> Dict:
        """执行使用物品命令"""
        if not args:
            return {
                "type": "error",
                "message": "请指定要使用的物品。用法: use <物品名称>"
            }
        
        item_name = " ".join(args)
        item_service = ItemService(db)
        return item_service.use_item(character, item_name)
