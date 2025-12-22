from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional

from .database import get_db, init_db
from .models import User, Character
from .schemas import UserCreate, UserResponse, Token, CharacterCreate, CharacterResponse
from .auth import (
    get_password_hash, verify_password, create_access_token,
    get_current_user, get_current_user_websocket, ACCESS_TOKEN_EXPIRE_MINUTES
)
from .game.commands import process_command
from .game.world import init_world
from .game.items import add_item_to_inventory
from .websocket.manager import manager

app = FastAPI(title="MUD RPG Game", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件挂载，提供网页前端
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    init_db()
    db = next(get_db())
    try:
        init_world(db)
        print("游戏世界初始化完成")
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
async def home_page():
    """门户首页"""
    return FileResponse("static/home.html")


@app.get("/auth", response_class=HTMLResponse)
async def auth_page():
    """登录 / 注册 页面"""
    return FileResponse("static/auth.html")


@app.get("/game", response_class=HTMLResponse)
async def game_page():
    """核心游戏页面"""
    return FileResponse("static/game.html")


@app.get("/info")
async def info():
    """保留原根路径的信息输出"""
    return {
        "message": "欢迎来到MUD RPG游戏！",
        "version": "1.0.0",
        "endpoints": {
            "register": "POST /register - 用户注册",
            "login": "POST /login - 用户登录",
            "character": "GET /character - 获取角色信息",
            "create_character": "POST /character/create - 创建角色",
            "websocket": "WS /ws?token=<token> - 游戏连接"
        }
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}


@app.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 创建新用户
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        password_hash=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@app.post("/login", response_model=Token)
async def login(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户登录"""
    # 验证用户
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/character", response_model=CharacterResponse)
async def get_character(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的角色"""
    character = db.query(Character).filter(Character.user_id == current_user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在，请先创建角色")
    return character


@app.post("/character/create", response_model=CharacterResponse)
async def create_character(
    character_data: CharacterCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建角色"""
    # 检查用户是否已有角色
    existing_character = db.query(Character).filter(Character.user_id == current_user.id).first()
    if existing_character:
        raise HTTPException(status_code=400, detail="你已有一个角色")
    
    # 检查角色名是否已存在
    existing_name = db.query(Character).filter(Character.name == character_data.name).first()
    if existing_name:
        raise HTTPException(status_code=400, detail="角色名已存在")
    
    # 创建新角色
    new_character = Character(
        user_id=current_user.id,
        name=character_data.name,
        level=1,
        hp=100,
        max_hp=100,
        mp=50,
        max_mp=50,
        exp=0,
        room_id=1,  # 默认在新手村
        attack=10,
        defense=5
    )
    db.add(new_character)
    db.commit()
    db.refresh(new_character)
    
    # 给新角色一些初始物品
    add_item_to_inventory(db, new_character, 1, 1)  # 木剑
    add_item_to_inventory(db, new_character, 5, 2)  # 治疗药水 x2
    
    return new_character


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """WebSocket游戏连接"""
    if not token:
        await websocket.close(code=1008, reason="缺少token")
        return
    
    # 创建数据库会话
    db = next(get_db())
    try:
        # 验证token并获取用户
        user = get_current_user_websocket(token, db)
        if not user:
            await websocket.close(code=1008, reason="无效的token")
            return
        
        # 获取角色
        character = db.query(Character).filter(Character.user_id == user.id).first()
        if not character:
            await websocket.send_json({
                "type": "error",
                "message": "请先创建角色"
            })
            await websocket.close(code=1008, reason="角色不存在")
            return
        
        # 建立连接
        await manager.connect(websocket, user.id, character.id, character.room_id)
        
        try:
            # 发送欢迎消息
            await websocket.send_json({
                "type": "info",
                "message": f"欢迎回来，{character.name}！输入 'help' 查看可用命令。"
            })
            
            # 发送当前房间信息
            from .game.player import look_room
            room_info = look_room(db, character)
            await websocket.send_json(room_info)
            
            # 处理消息循环
            while True:
                data = await websocket.receive_json()
                
                # 处理命令
                if "action" in data and data["action"] == "command":
                    command = data.get("data", "")
                    result = await process_command(db, character, command)
                    
                    # 发送结果
                    await websocket.send_json(result)
                    
                    # 刷新角色数据
                    db.refresh(character)
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": "无效的消息格式。请使用: {\"action\": \"command\", \"data\": \"<命令>\"}"
                    })
        
        except WebSocketDisconnect:
            manager.disconnect(user.id, character.id, character.room_id)
            
            # 通知房间内其他玩家
            await manager.broadcast_to_room(
                {
                    "type": "info",
                    "message": f"{character.name} 离开了游戏"
                },
                character.room_id,
                exclude_character_id=character.id,
                db=db
            )
        except Exception as e:
            print(f"WebSocket error for user={user.id} character={character.id}: {e}")
            manager.disconnect(user.id, character.id, character.room_id)
            await websocket.close(code=1011, reason="服务器错误")
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

