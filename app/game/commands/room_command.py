"""房间专属命令"""
from typing import Dict, Optional
from sqlalchemy.orm import Session
from ...models import Character, Command, RoomCommand
from .base_command import Command as BaseCommand
from ..services.config_service import ConfigService


class RoomCommandHandler(BaseCommand):
    """房间专属命令处理器"""
    
    def __init__(self):
        super().__init__("room", [])
    
    async def execute(
        self,
        db: Session,
        character: Character,
        args: list,
        command_key: str,
        **kwargs
    ) -> Dict:
        """执行房间专属命令"""
        # 查找命令定义
        cmd_entry = db.query(Command).filter(Command.key == command_key).first()
        if not cmd_entry:
            return {
                "type": "error",
                "message": f"未知的房间命令: {command_key}"
            }
        
        # 检查是否在当前房间绑定
        bound = (
            db.query(RoomCommand)
            .filter(
                RoomCommand.room_id == character.room_id,
                RoomCommand.command_id == cmd_entry.id,
            )
            .first()
        )
        if not bound:
            return {
                "type": "error",
                "message": f"当前房间不能使用命令: {command_key}"
            }
        
        # 根据 handler 执行相应逻辑
        handler = (cmd_entry.handler or "").lower()
        config_service = ConfigService(db)
        
        if handler == "room_train":
            # 训练命令
            character.exp += 10
            db.commit()
            return {
                "type": "success",
                "message": "你在训练场刻苦训练，获得了 10 点经验。",
                "data": {
                    "character": {
                        "name": character.name,
                        "level": character.level,
                        "hp": character.hp,
                        "max_hp": character.max_hp,
                        "mp": character.mp,
                        "max_mp": character.max_mp,
                        "attack": character.attack,
                        "defense": character.defense,
                        "exp": character.exp,
                    },
                    "available_commands": self._get_available_commands(db, character),
                },
            }
        elif handler == "room_study":
            # 学习命令
            old_mp = character.mp
            character.mp = min(character.max_mp, character.mp + 10)
            restored = character.mp - old_mp
            db.commit()
            return {
                "type": "success",
                "message": f"你在魔法学院研读卷轴，恢复了 {restored} 点魔法值。",
                "data": {
                    "character": {
                        "name": character.name,
                        "level": character.level,
                        "hp": character.hp,
                        "max_hp": character.max_hp,
                        "mp": character.mp,
                        "max_mp": character.max_mp,
                        "attack": character.attack,
                        "defense": character.defense,
                        "exp": character.exp,
                    },
                    "available_commands": self._get_available_commands(db, character),
                },
            }
        elif handler == "room_open_chest":
            # 打开宝箱命令
            return {
                "type": "success",
                "message": "你尝试打开宝箱，发现里面闪烁着微光……（具体掉落效果待实现）",
                "data": {
                    "available_commands": self._get_available_commands(db, character),
                },
            }
        else:
            return {
                "type": "error",
                "message": f"该房间命令暂未实现: {cmd_entry.key}"
            }
    
    def _get_available_commands(self, db: Session, character: Character) -> Dict:
        """获取可用命令"""
        from ..services.room_service import RoomService
        room_service = RoomService(db)
        return room_service.get_available_commands(character)
