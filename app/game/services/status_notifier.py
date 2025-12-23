"""角色状态变化通知服务 - 统一处理状态更新并主动发送消息"""
from typing import Optional, List
from sqlalchemy.orm import Session
from ...models import Character
from ...websocket.manager import manager
import asyncio


class CharacterStatusNotifier:
    """角色状态变化通知服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def notify_status_change(self, character: Character, reason: Optional[str] = None):
        """
        通知角色状态变化（异步方法）
        
        Args:
            character: 角色对象
            reason: 状态变化的原因（可选，用于调试）
        """
        # 刷新角色数据，确保获取最新状态
        self.db.refresh(character)
        
        # 检查角色是否在线
        if character.id not in manager.character_to_user:
            return  # 角色不在线，无需发送通知
        
        user_id = manager.character_to_user.get(character.id)
        if not user_id:
            return
        
        # 构建角色状态数据
        character_data = {
            "id": character.id,
            "name": character.name,
            "level": character.level,
            "hp": character.hp,
            "max_hp": character.max_hp,
            "mp": character.mp,
            "max_mp": character.max_mp,
            "exp": character.exp,
            "attack": character.attack,
            "defense": character.defense,
            "room_id": character.room_id
        }
        
        # 发送状态更新消息
        try:
            await manager.send_personal_message(
                {
                    "type": "status_update",
                    "message": reason or "角色状态已更新",
                    "character": character_data
                },
                user_id
            )
        except Exception as e:
            print(f"Error sending status update to character {character.id}: {e}")
    
    def notify_status_change_sync(self, character: Character, reason: Optional[str] = None):
        """
        通知角色状态变化（同步包装方法，可在同步上下文中调用）
        
        注意：这个方法会尝试在后台发送通知，如果失败会静默失败，不会阻塞调用者。
        
        Args:
            character: 角色对象
            reason: 状态变化的原因（可选，用于调试）
        """
        try:
            # 尝试获取当前事件循环
            try:
                loop = asyncio.get_running_loop()
                # 如果事件循环正在运行，创建后台任务（不等待）
                loop.create_task(self.notify_status_change(character, reason))
            except RuntimeError:
                # 如果没有运行中的事件循环，尝试获取或创建
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # 如果事件循环正在运行，创建后台任务
                        loop.create_task(self.notify_status_change(character, reason))
                    else:
                        # 如果事件循环未运行，直接运行
                        loop.run_until_complete(self.notify_status_change(character, reason))
                except RuntimeError:
                    # 如果没有事件循环，创建一个新的
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(self.notify_status_change(character, reason))
                    finally:
                        loop.close()
        except Exception as e:
            # 静默失败，不阻塞调用者
            # 只在调试时打印错误
            import os
            if os.getenv("DEBUG", "").lower() == "true":
                print(f"Error in notify_status_change_sync for character {character.id}: {e}")
    
    async def notify_multiple_characters(self, characters: List[Character], reason: Optional[str] = None):
        """
        批量通知多个角色的状态变化
        
        Args:
            characters: 角色对象列表
            reason: 状态变化的原因（可选）
        """
        for character in characters:
            await self.notify_status_change(character, reason)
    
    def notify_multiple_characters_sync(self, characters: List[Character], reason: Optional[str] = None):
        """
        批量通知多个角色的状态变化（同步包装方法）
        
        Args:
            characters: 角色对象列表
            reason: 状态变化的原因（可选）
        """
        for character in characters:
            self.notify_status_change_sync(character, reason)

