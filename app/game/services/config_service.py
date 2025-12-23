"""配置服务 - 提供配置缓存和访问"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ...repositories.config_repository import ConfigRepository


class ConfigCache:
    """配置缓存类"""
    _cache: Dict[str, Any] = {}
    _cache_time: Dict[str, datetime] = {}
    _ttl = timedelta(minutes=5)  # 5分钟缓存
    
    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key in cls._cache:
            if datetime.now() - cls._cache_time[key] < cls._ttl:
                return cls._cache[key]
            else:
                # 缓存过期，清除
                del cls._cache[key]
                del cls._cache_time[key]
        return None
    
    @classmethod
    def set(cls, key: str, value: Any):
        """设置缓存值"""
        cls._cache[key] = value
        cls._cache_time[key] = datetime.now()
    
    @classmethod
    def clear(cls):
        """清除所有缓存"""
        cls._cache.clear()
        cls._cache_time.clear()
    
    @classmethod
    def invalidate(cls, key: str):
        """使特定键的缓存失效"""
        if key in cls._cache:
            del cls._cache[key]
        if key in cls._cache_time:
            del cls._cache_time[key]


class ConfigService:
    """配置服务 - 提供配置的读取和缓存"""
    
    def __init__(self, db: Session):
        self.repository = ConfigRepository(db)
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值（带缓存）"""
        # 先检查缓存
        cached = ConfigCache.get(key)
        if cached is not None:
            return cached
        
        # 从数据库读取
        value = self.repository.get_value(key, default)
        if value is not None:
            ConfigCache.set(key, value)
        return value
    
    def get_combat_config(self) -> Dict[str, Any]:
        """获取战斗相关配置"""
        return {
            "attack_modifier_ratio": self.get_config("combat.attack_modifier_ratio", 0.5),
            "defense_reduction_ratio": self.get_config("combat.defense_reduction_ratio", 0.5),
            "damage_modifier_ratio": self.get_config("combat.damage_modifier_ratio", 0.33),
            "exp_gain_multiplier": self.get_config("combat.exp_gain_multiplier", 20),
        }
    
    def get_leveling_config(self) -> Dict[str, Any]:
        """获取升级相关配置"""
        return {
            "exp_per_level": self.get_config("leveling.exp_per_level", 100),
            "hp_per_level": self.get_config("leveling.hp_per_level", 20),
            "mp_per_level": self.get_config("leveling.mp_per_level", 10),
            "attack_per_level": self.get_config("leveling.attack_per_level", 2),
            "defense_per_level": self.get_config("leveling.defense_per_level", 1),
        }
    
    def set_config(self, key: str, value: Any, category: str = None, description: str = None):
        """设置配置（会清除缓存）"""
        self.repository.set_config(key, value, category, description)
        ConfigCache.invalidate(key)
    
    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self.repository.get_all_configs()
