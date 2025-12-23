"""房间服务 - 业务逻辑层"""
from typing import Dict, List
from sqlalchemy.orm import Session
from ...models import Character
from ...repositories.room_repository import RoomRepository
from ...repositories.config_repository import ConfigRepository


class RoomService:
    """房间服务 - 处理房间相关的业务逻辑"""
    
    def __init__(self, db: Session):
        self.db = db
        self.room_repo = RoomRepository(db)
    
    def get_available_commands(self, character: Character) -> Dict:
        """
        计算当前角色可执行的命令清单（用于前端 UI 展示）
        返回结构:
        {
            "global": [...],
            "movement": [...],
            "room": [...],
            "combat": [...]
        }
        """
        available = {
            "global": [],
            "movement": [],
            "room": [],
            "combat": [],
        }
        
        # movement: 根据当前房间出口生成
        room = self.room_repo.get_by_id(character.room_id)
        if room and room.exits:
            # exits 中存储的是英文方向，为避免歧义直接按 key 暴露
            available["movement"] = list(room.exits.keys())
        
        # global: 先简单写死基础常用命令，后续可从 Command 表筛选 category='global'
        available["global"] = ["help", "look", "stats", "inventory", "equipment", "say"]
        
        # room: 查询 RoomCommand 绑定的房间专属命令
        room_cmds = self.room_repo.get_available_commands(character.room_id)
        available["room"] = [c.key for c in room_cmds]
        
        # combat: 目前简单暴露攻击命令，未来可根据战斗状态动态调整
        available["combat"] = ["attack"]
        
        return available
