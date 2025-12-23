"""游戏世界定义 - 支持数据库初始化"""
from sqlalchemy.orm import Session
from ..models import Room, Item, Command, RoomCommand, GameConfig, NPC
from typing import Dict, List


# 预定义的房间数据（用于初始化）
ROOMS_DATA = [
    {
        "id": 1,
        "name": "新手村广场",
        "description": "一个热闹的广场，四周是古朴的建筑。这里是冒险者们的起点。",
        "exits": {"north": 2, "east": 3}
    },
    {
        "id": 2,
        "name": "武器店",
        "description": "一个充满铁锈味的武器店，墙上挂满了各种武器。店主正在擦拭一把长剑。",
        "exits": {"south": 1, "east": 4}
    },
    {
        "id": 3,
        "name": "魔法学院",
        "description": "古老的魔法学院，空气中弥漫着魔法的气息。书架上的魔法书闪闪发光。",
        "exits": {"west": 1, "north": 4}
    },
    {
        "id": 4,
        "name": "训练场",
        "description": "一个宽敞的训练场，地上散落着训练用的木桩。这里是提升实力的好地方。",
        "exits": {"south": 3, "west": 2, "north": 5},
        "special_properties": {"has_training_dummy": True}
    },
    {
        "id": 5,
        "name": "黑暗森林入口",
        "description": "一片阴森的森林，树木高大茂密，光线昏暗。远处传来奇怪的声响。",
        "exits": {"south": 4, "north": 6, "east": 7}
    },
    {
        "id": 6,
        "name": "森林深处",
        "description": "森林的最深处，这里充满了危险。你感觉到有东西在注视着你。",
        "exits": {"south": 5}
    },
    {
        "id": 7,
        "name": "神秘洞穴",
        "description": "一个神秘的洞穴入口，里面传来阵阵凉风。洞穴深处似乎有什么在发光。",
        "exits": {"west": 5, "north": 8}
    },
    {
        "id": 8,
        "name": "宝藏室",
        "description": "一个充满宝藏的房间！金光闪闪的宝箱堆满了角落。",
        "exits": {"south": 7}
    }
]

# 预定义的物品数据（用于初始化）
ITEMS_DATA = [
    {
        "id": 1,
        "name": "木剑",
        "description": "一把简单的木制长剑，适合新手使用。",
        "type": "weapon",
        "slot": "weapon",
        "stats": {"attack": 5},
        "value": 10
    },
    {
        "id": 2,
        "name": "铁剑",
        "description": "一把锋利的铁制长剑，攻击力更强。",
        "type": "weapon",
        "slot": "weapon",
        "stats": {"attack": 10},
        "value": 50
    },
    {
        "id": 3,
        "name": "布甲",
        "description": "简单的布制护甲，提供基本的防护。",
        "type": "armor",
        "slot": "chest",
        "stats": {"defense": 3},
        "value": 15
    },
    {
        "id": 4,
        "name": "皮甲",
        "description": "用皮革制成的护甲，比布甲更坚固。",
        "type": "armor",
        "slot": "chest",
        "stats": {"defense": 6},
        "value": 40
    },
    {
        "id": 5,
        "name": "治疗药水",
        "description": "一瓶红色的治疗药水，可以恢复50点生命值。",
        "type": "consumable",
        "slot": None,
        "stats": {"hp": 50},
        "value": 20
    },
    {
        "id": 6,
        "name": "魔法药水",
        "description": "一瓶蓝色的魔法药水，可以恢复30点魔法值。",
        "type": "consumable",
        "slot": None,
        "stats": {"mp": 30},
        "value": 15
    },
    {
        "id": 7,
        "name": "铁头盔",
        "description": "一顶坚固的铁制头盔，保护头部。",
        "type": "armor",
        "slot": "head",
        "stats": {"defense": 4},
        "value": 30
    },
    {
        "id": 8,
        "name": "魔法法杖",
        "description": "一根镶嵌着魔法水晶的法杖，增强魔法攻击。",
        "type": "weapon",
        "slot": "weapon",
        "stats": {"attack": 8, "mp": 20},
        "value": 80
    }
]

# 游戏配置数据（用于初始化）
GAME_CONFIG_DATA = [
    {
        "key": "combat.attack_modifier_ratio",
        "value": 0.5,
        "category": "combat",
        "description": "攻击力修正比例（用于命中判定）"
    },
    {
        "key": "combat.defense_reduction_ratio",
        "value": 0.5,
        "category": "combat",
        "description": "防御减免比例"
    },
    {
        "key": "combat.damage_modifier_ratio",
        "value": 0.33,
        "category": "combat",
        "description": "伤害修正比例"
    },
    {
        "key": "combat.exp_gain_multiplier",
        "value": 20,
        "category": "combat",
        "description": "击败敌人经验倍数"
    },
    {
        "key": "leveling.exp_per_level",
        "value": 100,
        "category": "leveling",
        "description": "每级所需经验倍数"
    },
    {
        "key": "leveling.hp_per_level",
        "value": 20,
        "category": "leveling",
        "description": "每级HP提升"
    },
    {
        "key": "leveling.mp_per_level",
        "value": 10,
        "category": "leveling",
        "description": "每级MP提升"
    },
    {
        "key": "leveling.attack_per_level",
        "value": 2,
        "category": "leveling",
        "description": "每级攻击提升"
    },
    {
        "key": "leveling.defense_per_level",
        "value": 1,
        "category": "leveling",
        "description": "每级防御提升"
    },
]

# NPC数据（用于初始化）
NPC_DATA = [
    {
        "name": "测试靶子",
        "type": "training_dummy",
        "room_id": 4,  # 训练场
        "properties": {
            "defense": 0,
            "max_hp": 1000,
            "hp": 1000,
            "is_invincible": True
        }
    }
]


def init_world(db: Session):
    """初始化游戏世界"""
    # 初始化房间
    for room_data in ROOMS_DATA:
        existing_room = db.query(Room).filter(Room.id == room_data["id"]).first()
        if not existing_room:
            room = Room(
                id=room_data["id"],
                name=room_data["name"],
                description=room_data["description"],
                exits=room_data["exits"],
                special_properties=room_data.get("special_properties", {})
            )
            db.add(room)
    
    # 初始化物品
    for item_data in ITEMS_DATA:
        existing_item = db.query(Item).filter(Item.id == item_data["id"]).first()
        if not existing_item:
            item = Item(
                id=item_data["id"],
                name=item_data["name"],
                description=item_data["description"],
                type=item_data["type"],
                slot=item_data["slot"],
                stats=item_data["stats"],
                value=item_data["value"]
            )
            db.add(item)
    
    # 初始化游戏配置
    for config_data in GAME_CONFIG_DATA:
        existing_config = db.query(GameConfig).filter(GameConfig.key == config_data["key"]).first()
        if not existing_config:
            config = GameConfig(
                key=config_data["key"],
                value=config_data["value"],
                category=config_data["category"],
                description=config_data["description"]
            )
            db.add(config)
    
    # 初始化NPC
    for npc_data in NPC_DATA:
        existing_npc = db.query(NPC).filter(
            NPC.name == npc_data["name"],
            NPC.room_id == npc_data["room_id"]
        ).first()
        if not existing_npc:
            npc = NPC(
                name=npc_data["name"],
                type=npc_data["type"],
                room_id=npc_data["room_id"],
                properties=npc_data["properties"]
            )
            db.add(npc)
    
    db.commit()

    # 初始化基础指令与房间绑定（配置化房间指令示例）
    init_commands_and_room_bindings(db)


def init_commands_and_room_bindings(db: Session):
    """初始化基础命令定义以及房间与命令的绑定"""
    # 已存在的命令缓存，避免重复查询
    existing_commands = {
        c.key: c for c in db.query(Command).all()
    }

    def get_or_create_command(
        key: str,
        category: str,
        description: str = "",
        aliases: List[str] | None = None,
        handler: str | None = None,
    ) -> Command:
        cmd = existing_commands.get(key)
        if cmd:
            return cmd

        cmd = Command(
            key=key,
            category=category,
            description=description,
            aliases=aliases or [],
            handler=handler,
        )
        db.add(cmd)
        db.flush()  # 立即获得 id
        existing_commands[key] = cmd
        return cmd

    # 示例：一些通用全局命令定义（即使不通过 RoomCommand 绑定，也可用于 help/前端展示）
    get_or_create_command(
        key="look",
        category="global",
        description="观察当前房间。",
        aliases=["l"],
        handler="look",
    )
    get_or_create_command(
        key="stats",
        category="global",
        description="查看角色属性。",
        aliases=["status", "stat"],
        handler="stats",
    )
    get_or_create_command(
        key="inventory",
        category="global",
        description="查看物品栏。",
        aliases=["inv", "bag", "items"],
        handler="inventory",
    )
    get_or_create_command(
        key="equipment",
        category="global",
        description="查看当前装备。",
        aliases=["equipments", "eq"],
        handler="equipment",
    )
    get_or_create_command(
        key="say",
        category="global",
        description="在当前房间说话。",
        aliases=["speak", "talk"],
        handler="say",
    )
    get_or_create_command(
        key="help",
        category="global",
        description="查看帮助信息。",
        aliases=["h", "?"],
        handler="help",
    )

    # 示例：房间专属命令
    # 训练场: id=4，命令 train
    train_cmd = get_or_create_command(
        key="train",
        category="room",
        description="在训练场进行基础训练，获得少量经验。",
        aliases=[],
        handler="room_train",
    )

    # 魔法学院: id=3，命令 study
    study_cmd = get_or_create_command(
        key="study",
        category="room",
        description="在魔法学院学习，获得魔力相关收益。",
        aliases=[],
        handler="room_study",
    )

    # 神秘洞穴 / 宝藏室: id=7/8，命令 open_chest
    chest_cmd = get_or_create_command(
        key="open_chest",
        category="room",
        description="尝试打开附近的宝箱。",
        aliases=[],
        handler="room_open_chest",
    )

    # 当前已存在的房间绑定，避免重复插入
    existing_room_cmd_pairs = {
        (rc.room_id, rc.command_id) for rc in db.query(RoomCommand).all()
    }

    def bind(room_id: int, cmd: Command):
        pair = (room_id, cmd.id)
        if pair in existing_room_cmd_pairs:
            return
        rc = RoomCommand(room_id=room_id, command_id=cmd.id, conditions={})
        db.add(rc)
        existing_room_cmd_pairs.add(pair)

    # 训练场房间绑定 train
    bind(4, train_cmd)
    # 魔法学院绑定 study
    bind(3, study_cmd)
    # 神秘洞穴与宝藏室绑定 open_chest
    bind(7, chest_cmd)
    bind(8, chest_cmd)

    db.commit()


def get_room_by_id(db: Session, room_id: int) -> Room:
    """根据ID获取房间"""
    return db.query(Room).filter(Room.id == room_id).first()


def get_room_exits(room: Room) -> Dict[str, str]:
    """获取房间出口方向名称"""
    if not room or not room.exits:
        return {}
    
    exit_names = {}
    direction_map = {
        "north": "北",
        "south": "南",
        "east": "东",
        "west": "西"
    }
    
    for direction, target_room_id in room.exits.items():
        exit_names[direction_map.get(direction, direction)] = target_room_id
    
    return exit_names