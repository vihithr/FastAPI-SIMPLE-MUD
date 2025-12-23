"""消息构建器基类"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class MessageBuilder(ABC):
    """消息构建器基类"""
    
    @abstractmethod
    def build(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """构建消息"""
        pass
    
    @staticmethod
    def create_message(
        message_type: str,
        message: str,
        data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """创建标准消息格式"""
        result = {
            "type": message_type,
            "message": message
        }
        if data:
            result["data"] = data
        return result
    
    @staticmethod
    def create_error(message: str) -> Dict[str, Any]:
        """创建错误消息"""
        return MessageBuilder.create_message("error", message)
    
    @staticmethod
    def create_success(message: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """创建成功消息"""
        return MessageBuilder.create_message("success", message, data)
    
    @staticmethod
    def create_info(message: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """创建信息消息"""
        return MessageBuilder.create_message("info", message, data)
