"""命令模块"""
from .command_registry import CommandRegistry, registry
from .base_command import Command
from sqlalchemy.orm import Session
from ...models import Character
from ...websocket.manager import manager


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
    from ..services.room_service import RoomService
    room_service = RoomService(db)
    return room_service.get_available_commands(character)


async def process_command(db: Session, character: Character, command: str) -> dict:
    """处理玩家命令 - 使用命令模式"""
    if not command or not command.strip():
        return {
            "type": "error",
            "message": "请输入命令"
        }

    parts = command.strip().split()
    raw_cmd = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []

    # 检查是否是移动命令（特殊处理，因为移动命令需要特殊格式）
    movement_direction = _normalize_movement_command(raw_cmd)
    if movement_direction is not None:
        # 使用命令模式处理移动
        result = await registry.execute_command(db, character, "move", [movement_direction])
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

    # 使用命令注册表执行命令
    result = await registry.execute_command(db, character, raw_cmd, args)
    
    # 特殊处理：战斗命令需要额外的通知逻辑
    if raw_cmd in ["attack", "hit", "fight"] and result.get("type") == "combat":
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


__all__ = ["CommandRegistry", "registry", "Command", "process_command", "get_available_commands"]