"""命令基类"""
from abc import ABC, abstractmethod
from typing import Dict, Optional
from sqlalchemy.orm import Session
from ...models import Character


class Command(ABC):
    """命令基类"""
    
    def __init__(self, name: str, aliases: list = None):
        self.name = name
        self.aliases = aliases or []
    
    def matches(self, command: str) -> bool:
        """检查命令是否匹配"""
        cmd_lower = command.lower()
        return cmd_lower == self.name.lower() or cmd_lower in [a.lower() for a in self.aliases]
    
    @abstractmethod
    async def execute(
        self,
        db: Session,
        character: Character,
        args: list,
        **kwargs
    ) -> Dict:
        """执行命令"""
        pass
    
    def validate_args(self, args: list, min_args: int = 0, max_args: int = None) -> bool:
        """验证参数数量"""
        if len(args) < min_args:
            return False
        if max_args is not None and len(args) > max_args:
            return False
        return True
