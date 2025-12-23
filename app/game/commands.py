"""命令解析和处理"""
from sqlalchemy.orm import Session
from ..models import Character, Command, RoomCommand, Room
from .player import move_character, look_room, get_character_stats
from .combat import attack_character
from .items import (
    get_character_inventory, equip_item, unequip_item, use_item, get_character_equipment
)
from ..websocket.manager import manager
from .world import get_room_by_id


def _normalize_movement_command(cmd: str) -> str | None:
    """将移动相关命令标准化为方向 key，如 'north'/'south'"""
    direction_map = {
        "north": "north",
        "n": "north",
        "south": "south",
        "s": "south",
        "east": "east",
        "e": "east",
        "west": "west",
        "w": "west",
    }
    return direction_map.get(cmd.lower())


def get_available_commands(db: Session, character: Character) -> dict:
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
    room: Room | None = get_room_by_id(db, character.room_id)
    if room and room.exits:
        # exits 中存储的是英文方向，为避免歧义直接按 key 暴露
        available["movement"] = list(room.exits.keys())

    # global: 先简单写死基础常用命令，后续可从 Command 表筛选 category='global'
    available["global"] = ["help", "look", "stats", "inventory", "equipment", "say"]

    # room: 查询 RoomCommand 绑定的房间专属命令
    room_cmds = (
        db.query(Command)
        .join(RoomCommand, RoomCommand.command_id == Command.id)
        .filter(RoomCommand.room_id == character.room_id)
        .all()
    )
    available["room"] = [c.key for c in room_cmds]

    # combat: 目前简单暴露攻击命令，未来可根据战斗状态动态调整
    available["combat"] = ["attack"]

    return available


async def process_command(db: Session, character: Character, command: str) -> dict:
    """处理玩家命令"""
    if not command or not command.strip():
        return {
            "type": "error",
            "message": "请输入命令"
        }

    parts = command.strip().split()
    raw_cmd = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []

    # 1. 移动命令：仍然使用现有 move_character 逻辑，并在结果中附带 available_commands
    movement_direction = _normalize_movement_command(raw_cmd)
    if movement_direction is not None:
        result = move_character(db, character, movement_direction)
        if result["type"] == "success":
            # 附带当前可用指令
            result.setdefault("data", {})
            result["data"]["available_commands"] = get_available_commands(db, character)

            # 通知房间内其他玩家
            await manager.broadcast_to_room(
                {
                    "type": "info",
                    "message": f"{character.name} 进入了房间"
                },
                character.room_id,
                exclude_character_id=character.id,
                db=db
            )
        return result

    # 2. 根据 Command/RoomCommand 做房间专属指令判断（仅限 category='room'）
    # 先尝试在 Command 表中解析标准命令 key（含别名）
    cmd_entry: Command | None = (
        db.query(Command)
        .filter(
            (Command.key == raw_cmd) |
            (Command.aliases.contains([raw_cmd]))  # 简单用 contains 匹配
        )
        .first()
    )

    # 房间专属命令：必须在当前房间绑定了对应 Command
    if cmd_entry and cmd_entry.category == "room":
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
                "message": f"当前房间不能使用命令: {raw_cmd}"
            }

        # 根据 handler 跳转到具体逻辑，当前做一个占位实现
        handler = (cmd_entry.handler or "").lower()
        if handler == "room_train":
            # 简单示例: 给少量经验
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
                    "available_commands": get_available_commands(db, character),
                },
            }
        elif handler == "room_study":
            # 示例: 恢复少量 MP
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
                    "available_commands": get_available_commands(db, character),
                },
            }
        elif handler == "room_open_chest":
            # 示例: 仅给出 flavor 文本，掉落逻辑可后续扩展
            return {
                "type": "success",
                "message": "你尝试打开宝箱，发现里面闪烁着微光……（具体掉落效果待实现）",
                "data": {
                    "available_commands": get_available_commands(db, character),
                },
            }
        else:
            return {
                "type": "error",
                "message": f"该房间命令暂未实现: {cmd_entry.key}"
            }

    # 3. 兼容现有基础命令（global/combat 等），逻辑保持原样，仅在合适时附带 available_commands

    # 查看房间
    if raw_cmd in ["look", "l"]:
        result = look_room(db, character)
        # 附带可用命令
        result.setdefault("data", {})
        result["data"]["available_commands"] = get_available_commands(db, character)
        return result

    # 查看属性
    if raw_cmd in ["stats", "status", "stat"]:
        return get_character_stats(character)

    # 攻击命令
    if raw_cmd in ["attack", "hit", "fight"]:
        if not args:
            return {
                "type": "error",
                "message": "请指定攻击目标。用法: attack <目标名称>"
            }
        target_name = " ".join(args)
        result = attack_character(db, character, target_name)

        # 如果战斗成功，通知防御者（排除测试靶子和自己）
        if result.get("defender_id") and result.get("defender_message") and not result.get("data", {}).get("is_training_dummy"):
            defender_id = result["defender_id"]
            # 确保不是攻击自己，并且防御者在线
            if defender_id != character.id and defender_id in manager.character_to_user:
                user_id = manager.character_to_user[defender_id]
                try:
                    await manager.send_personal_message(
                        {
                            "type": "combat",
                            "message": result["defender_message"],
                            "data": result.get("data", {})
                        },
                        user_id
                    )
                except Exception as e:
                    print(f"Error sending combat message to defender {defender_id}: {e}")

        # 广播战斗消息到房间（排除测试靶子）
        if result["type"] == "combat" and not result.get("data", {}).get("is_training_dummy"):
            try:
                await manager.broadcast_to_room(
                    {
                        "type": "info",
                        "message": f"{character.name} 攻击了 {result['data'].get('defender', '目标')}"
                    },
                    character.room_id,
                    exclude_character_id=character.id,
                    db=db
                )
            except Exception as e:
                print(f"Error broadcasting combat message: {e}")

        return result

    # 装备物品
    if raw_cmd in ["equip", "wear"]:
        if not args:
            return {
                "type": "error",
                "message": "请指定要装备的物品。用法: equip <物品名称>"
            }
        item_name = " ".join(args)
        return equip_item(db, character, item_name)

    # 卸下装备
    if raw_cmd in ["unequip", "remove"]:
        if not args:
            return {
                "type": "error",
                "message": "请指定要卸下的装备槽位。用法: unequip <槽位>"
            }
        slot = args[0].lower()
        return unequip_item(db, character, slot)

    # 使用物品
    if raw_cmd in ["use", "drink", "eat"]:
        if not args:
            return {
                "type": "error",
                "message": "请指定要使用的物品。用法: use <物品名称>"
            }
        item_name = " ".join(args)
        return use_item(db, character, item_name)

    # 查看物品栏
    if raw_cmd in ["inventory", "inv", "bag", "items"]:
        inventory = get_character_inventory(db, character)
        if not inventory:
            return {
                "type": "info",
                "message": "你的物品栏是空的",
                "data": {"inventory": []}
            }

        items_text = "\n".join([
            f"- {item['name']} x{item['quantity']} ({item['type']})"
            for item in inventory
        ])

        return {
            "type": "info",
            "message": f"物品栏:\n{items_text}",
            "data": {"inventory": inventory}
        }

    # 查看装备
    if raw_cmd in ["equipment", "equipments", "eq"]:
        equipment = get_character_equipment(db, character)
        if not equipment:
            return {
                "type": "info",
                "message": "你没有装备任何物品",
                "data": {"equipment": {}}
            }

        eq_text = "\n".join([
            f"- {slot}: {item['name']}"
            for slot, item in equipment.items()
        ])

        return {
            "type": "info",
            "message": f"当前装备:\n{eq_text}",
            "data": {"equipment": equipment}
        }

    # 说话
    if raw_cmd in ["say", "speak", "talk"]:
        if not args:
            return {
                "type": "error",
                "message": "请指定要说的话。用法: say <消息>"
            }
        message = " ".join(args)

        # 广播到房间
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

    # 帮助命令
    if raw_cmd in ["help", "h", "?"]:
        # 简单根据当前可用命令拼出一个帮助文本
        available = get_available_commands(db, character)
        help_lines = [
            "可用命令:",
            f"  移动: {', '.join(available.get('movement') or ['无'])}",
            "  查看: look(l), stats, inventory(inv), equipment(eq)",
            "  战斗: attack <目标>",
            "  物品: equip <物品>, unequip <槽位>, use <物品>",
            "  社交: say <消息>",
        ]
        if available.get("room"):
            help_lines.append(f"  房间: {', '.join(available['room'])}")

        return {
            "type": "info",
            "message": "\n".join(help_lines)
        }

    # 未知命令
    return {
        "type": "error",
        "message": f"未知命令: {raw_cmd}。输入 'help' 查看可用命令"
    }

