"""配置Repository"""
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from ..models import GameConfig
from .base_repository import BaseRepository


class ConfigRepository(BaseRepository[GameConfig]):
    """游戏配置数据访问层"""
    
    def __init__(self, db: Session):
        super().__init__(db, GameConfig)
    
    def get_by_key(self, key: str) -> Optional[GameConfig]:
        """根据键获取配置"""
        return self.db.query(GameConfig).filter(GameConfig.key == key).first()
    
    def get_value(self, key: str, default=None):
        """获取配置值"""
        config = self.get_by_key(key)
        return config.value if config else default
    
    def get_by_category(self, category: str) -> List[GameConfig]:
        """根据分类获取配置列表"""
        return self.db.query(GameConfig).filter(GameConfig.category == category).all()
    
    def get_all_configs(self) -> Dict[str, any]:
        """获取所有配置（返回字典格式）"""
        configs = self.get_all(limit=1000)  # 假设配置不会超过1000条
        return {config.key: config.value for config in configs}
    
    def set_config(self, key: str, value: any, category: str = None, description: str = None) -> GameConfig:
        """设置配置（如果不存在则创建，存在则更新）"""
        config = self.get_by_key(key)
        if config:
            config.value = value
            if category:
                config.category = category
            if description:
                config.description = description
            return self.update(config)
        else:
            new_config = GameConfig(
                key=key,
                value=value,
                category=category or "general",
                description=description or ""
            )
            return self.create(new_config)
