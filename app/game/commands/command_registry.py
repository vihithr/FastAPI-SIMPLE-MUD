"""命令注册表"""
from typing import Dict, Optional
from sqlalchemy.orm import Session
from ...models import Character
from .base_command import Command
from .movement_command import MovementCommand
from .combat_command import CombatCommand
from .look_command import LookCommand
from .stats_command import StatsCommand
from .inventory_command import InventoryCommand
from .equipment_command import EquipmentCommand
from .equip_command import EquipCommand
from .unequip_command import UnequipCommand
from .use_command import UseCommand
from .say_command import SayCommand
from .help_command import HelpCommand
from .flee_command import FleeCommand
from .room_command import RoomCommandHandler


class CommandRegistry:
    """命令注册表 - 管理所有命令"""
    
    def __init__(self):
        self._commands: Dict[str, Command] = {}
        self._register_default_commands()
    
    def _register_default_commands(self):
        """注册默认命令"""
        commands = [
            MovementCommand(),
            CombatCommand(),
            LookCommand(),
            StatsCommand(),
            InventoryCommand(),
            EquipmentCommand(),
            EquipCommand(),
            UnequipCommand(),
            UseCommand(),
            SayCommand(),
            HelpCommand(),
            FleeCommand(),
        ]
        
        for cmd in commands:
            self.register(cmd)
    
    def register(self, command: Command):
        """注册命令"""
        self._commands[command.name.lower()] = command
        for alias in command.aliases:
            self._commands[alias.lower()] = command
    
    def get_command(self, command_name: str) -> Optional[Command]:
        """获取命令"""
        return self._commands.get(command_name.lower())
    
    async def execute_command(
        self,
        db: Session,
        character: Character,
        command: str,
        args: list = None
    ) -> Dict:
        """执行命令"""
        if not command:
            return {
                "type": "error",
                "message": "请输入命令"
            }
        
        cmd = self.get_command(command)
        if cmd:
            return await cmd.execute(db, character, args or [])
        
        # 如果不是已注册的命令，检查是否是房间专属命令
        from ...models import Command as CommandModel, RoomCommand
        cmd_entry = (
            db.query(CommandModel)
            .filter(
                (CommandModel.key == command) |
                (CommandModel.aliases.contains([command]))
            )
            .first()
        )
        
        if cmd_entry and cmd_entry.category == "room":
            room_handler = RoomCommandHandler()
            return await room_handler.execute(db, character, args or [], command)
        
        return {
            "type": "error",
            "message": f"未知命令: {command}。输入 'help' 查看可用命令"
        }


# 全局命令注册表实例
registry = CommandRegistry()
