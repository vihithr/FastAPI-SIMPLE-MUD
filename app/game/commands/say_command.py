"""说话命令"""
from typing import Dict
from sqlalchemy.orm import Session
from ...models import Character
from .base_command import Command


class SayCommand(Command):
    """说话命令"""
    
    def __init__(self):
        super().__init__("say", ["speak", "talk"])
    
    async def execute(
        self,
        db: Session,
        character: Character,
        args: list,
        **kwargs
    ) -> Dict:
        """执行说话命令"""
        if not args:
            return {
                "type": "error",
                "message": "请指定要说的话。用法: say <消息>"
            }
        
        message = " ".join(args)
        
        # 广播到房间
        from ...websocket.manager import manager
        await manager.broadcast_to_room(
            {
                "type": "info",
                "message": f"{character.name} 说: {message}"
            },
            character.room_id,
            exclude_character_id=None,  # 包括自己
            db=db
        )
        
        return {
            "type": "success",
            "message": f"你说: {message}"
        }
