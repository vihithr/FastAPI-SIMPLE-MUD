from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class CharacterCreate(BaseModel):
    name: str


class CharacterResponse(BaseModel):
    id: int
    name: str
    level: int
    hp: int
    max_hp: int
    mp: int
    max_mp: int
    exp: int
    room_id: int
    attack: int
    defense: int

    class Config:
        from_attributes = True


class RoomResponse(BaseModel):
    id: int
    name: str
    description: str
    exits: Dict[str, int]

    class Config:
        from_attributes = True


class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    type: str
    slot: Optional[str]
    stats: Dict
    value: int

    class Config:
        from_attributes = True


class InventoryResponse(BaseModel):
    id: int
    item: ItemResponse
    quantity: int

    class Config:
        from_attributes = True


class EquipmentResponse(BaseModel):
    slot: str
    item: ItemResponse

    class Config:
        from_attributes = True


class WebSocketMessage(BaseModel):
    action: str
    data: Optional[str] = None
    target: Optional[str] = None


class GameMessage(BaseModel):
    type: str  # info, error, success, combat, room
    message: str
    data: Optional[Dict] = None

