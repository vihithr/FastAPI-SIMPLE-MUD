from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    """用户账户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    characters = relationship("Character", back_populates="user", cascade="all, delete-orphan")


class Character(Base):
    """角色表"""
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(50), unique=True, index=True, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    hp = Column(Integer, default=100, nullable=False)
    max_hp = Column(Integer, default=100, nullable=False)
    mp = Column(Integer, default=50, nullable=False)
    max_mp = Column(Integer, default=50, nullable=False)
    exp = Column(Integer, default=0, nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), default=1, nullable=False)
    attack = Column(Integer, default=10, nullable=False)
    defense = Column(Integer, default=5, nullable=False)
    # 战斗状态字段
    in_combat_with = Column(Integer, ForeignKey("characters.id"), nullable=True)  # 正在与谁战斗
    combat_turn = Column(Integer, default=0)  # 战斗轮次计数
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    user = relationship("User", back_populates="characters")
    room = relationship("Room", back_populates="characters")
    inventory_items = relationship("Inventory", back_populates="character", cascade="all, delete-orphan")
    equipment_items = relationship("Equipment", back_populates="character", cascade="all, delete-orphan")


class Room(Base):
    """房间/地点表"""
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    exits = Column(JSON, default={})  # {"north": 2, "south": 1, ...}
    special_properties = Column(JSON, default={})  # 房间特殊属性，如训练靶子等

    # 关系
    characters = relationship("Character", back_populates="room")
    room_commands = relationship("RoomCommand", back_populates="room", cascade="all, delete-orphan")
    npcs = relationship("NPC", back_populates="room", cascade="all, delete-orphan")


class Item(Base):
    """物品定义表"""
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    type = Column(String(50), nullable=False)  # weapon, armor, consumable
    slot = Column(String(50))  # weapon, head, chest, legs, feet (for equipment)
    stats = Column(JSON, default={})  # {"attack": 5, "defense": 3, "hp": 20, ...}
    value = Column(Integer, default=0)  # 物品价值

    # 关系
    inventory_items = relationship("Inventory", back_populates="item")
    equipment_items = relationship("Equipment", back_populates="item")


class Inventory(Base):
    """角色物品栏表"""
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)

    # 关系
    character = relationship("Character", back_populates="inventory_items")
    item = relationship("Item", back_populates="inventory_items")


class Equipment(Base):
    """角色装备表"""
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    slot = Column(String(50), nullable=False)  # weapon, head, chest, legs, feet
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)

    # 关系
    character = relationship("Character", back_populates="equipment_items")
    item = relationship("Item", back_populates="equipment_items")


class CombatLog(Base):
    """战斗记录表"""
    __tablename__ = "combat_logs"

    id = Column(Integer, primary_key=True, index=True)
    attacker_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    defender_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    damage = Column(Integer, nullable=False)
    attacker_hp_after = Column(Integer)
    defender_hp_after = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class Command(Base):
    """可复用指令定义表"""
    __tablename__ = "commands"

    id = Column(Integer, primary_key=True, index=True)
    # 主命令 key，如: look / stats / train
    key = Column(String(50), unique=True, index=True, nullable=False)
    # 别名列表，例如 ["l"]，使用 JSON 方便扩展
    aliases = Column(JSON, default=[])
    # 指令类别: movement/global/room/combat 等
    category = Column(String(50), nullable=False, default="global")
    # 文本描述，给 help/前端 UI 用
    description = Column(Text, default="")
    # 处理逻辑标记，可选，例如 "look", "stats", "room_train"
    handler = Column(String(100), nullable=True)

    # 关系
    room_commands = relationship("RoomCommand", back_populates="command", cascade="all, delete-orphan")


class RoomCommand(Base):
    """房间与指令的多对多绑定表"""
    __tablename__ = "room_commands"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    command_id = Column(Integer, ForeignKey("commands.id"), nullable=False)
    # 预留条件字段，后续可用于等级/任务前置等
    conditions = Column(JSON, default={})

    # 关系
    room = relationship("Room", back_populates="room_commands")
    command = relationship("Command", back_populates="room_commands")


class GameConfig(Base):
    """游戏配置表 - 存储所有可配置的游戏规则"""
    __tablename__ = "game_config"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)  # 配置键
    value = Column(JSON, nullable=False)  # 配置值（支持复杂结构）
    category = Column(String(50), index=True)  # 分类：combat, leveling, world等
    description = Column(Text)  # 配置说明
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class NPC(Base):
    """NPC表 - 包括训练靶子、商店NPC等"""
    __tablename__ = "npcs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), index=True)  # training_dummy, shopkeeper, quest_giver等
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    # NPC属性（JSON格式，灵活存储不同类型NPC的数据）
    properties = Column(JSON, default={})
    # 例如训练靶子: {"defense": 0, "max_hp": 1000, "hp": 1000, "is_invincible": true}
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    room = relationship("Room", back_populates="npcs")
