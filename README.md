# MUD RPG 游戏

基于 FastAPI 的多人在线文字 RPG（MUD）示例，支持 JWT 认证、WebSocket 实时交互以及静态网页界面。

## 核心特性
- 用户注册/登录（JWT），每个账号限创建一个角色
- 角色创建、属性查看与升级（击败玩家获得经验，经验=100×等级时自动升级）
- 多房间世界（8 个房间，含训练/学习/宝箱等房间专属指令）
- 物品与装备系统（武器、防具、消耗品；装备加成；药水恢复）
- 回合制 PvP 战斗与房间广播
- WebSocket 指令驱动：移动、观察、聊天、战斗、物品、房间交互
- 静态前端：`/` 首页、`/auth` 登录注册页、`/game` 游戏页

## 技术栈
- FastAPI + Uvicorn
- SQLAlchemy + SQLite（`mud_game.db` 自动创建并初始化）
- WebSocket（原生 FastAPI）
- JWT（python-jose）+ passlib(bcrypt)
- 前端静态 HTML/JS（见 `static/`）

## 目录结构
```
app/
├── main.py              # FastAPI 入口，挂载静态页、REST 与 WebSocket
├── auth.py              # JWT 认证
├── database.py          # SQLite 连接与初始化
├── models.py            # ORM 模型（用户、角色、房间、物品等）
├── schemas.py           # Pydantic 模型
├── game/                # 游戏逻辑
│   ├── world.py         # 房间/物品/命令初始化
│   ├── player.py        # 移动、查看房间、属性
│   ├── combat.py        # 战斗、经验与升级
│   ├── items.py         # 物品栏、装备、使用
│   └── commands.py      # 指令解析与房间专属命令
└── websocket/           # 连接管理
    └── manager.py
static/                  # 前端页面与 JS
requirements.txt
README.md
```

## 快速开始
1) 安装依赖
```bash
pip install -r requirements.txt
```

2) 启动（仓库根目录执行）
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

3) 访问
- 首页：`http://localhost:8000/`
- 登录/注册页：`http://localhost:8000/auth`
- 游戏页：`http://localhost:8000/game`
- API 文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/health`

> 首次启动会自动初始化 SQLite 数据库、房间、物品以及房间专属命令。

## 认证流程
1) 注册：`POST /register`
```json
{ "username": "player1", "password": "password123" }
```
2) 登录获取 JWT：`POST /login`
```json
{ "username": "player1", "password": "password123" }
```
返回 `access_token`，REST 请求在头部携带 `Authorization: Bearer <token>`，WebSocket 连接使用 `ws://localhost:8000/ws?token=<token>`。

## REST API
- `POST /register` 注册
- `POST /login` 登录并获取 JWT
- `GET /info` 应用信息
- `GET /character` 获取角色（需登录）
- `POST /character/create` 创建角色（需登录）
- `GET /health` 健康检查

## WebSocket 协议
连接：`WS /ws?token=<jwt_token>`

发送格式：
```json
{ "action": "command", "data": "look" }
```

常用命令：
- 移动：`north(n) | south(s) | east(e) | west(w)`
- 查看：`look(l)` 查看房间；`stats` 查看属性
- 物品：`inventory(inv)` 查看物品栏；`equipment(eq)` 查看装备；`equip <物品>`；`unequip <槽位>`；`use <物品>`
- 战斗：`attack <玩家名称>`（同房间且在线）
- 社交：`say <内容>`（房间广播）
- 帮助：`help`
- 房间专属：`train`（训练场，+10 经验）、`study`（魔法学院，恢复少量 MP）、`open_chest`（神秘洞穴/宝藏室，示例事件）

部分响应会附带 `available_commands`，便于前端直接渲染当前可用指令。

## 游戏世界与内容
- 房间（8）：新手村广场、武器店、魔法学院、训练场、黑暗森林入口、森林深处、神秘洞穴、宝藏室
- 初始物品：木剑 ×1，治疗药水 ×2
- 物品：木剑/铁剑/魔法法杖，布甲/皮甲/铁头盔，治疗药水/魔法药水
- 战斗：伤害含随机波动与防御减免；击败玩家获得 `20×对方等级` 经验，达到 `100×等级` 经验自动升级并回复生命/魔力，提升攻防与上限

## 注意事项
- 生产环境请修改 `app/auth.py` 的 `SECRET_KEY`，或改为读取环境变量
- 每个账号仅允许一个角色，角色名全局唯一
- WebSocket 需要有效 JWT，战斗需双方在线且在同一房间
- 数据保存在仓库根目录的 `mud_game.db`，删除即可重置

## 示例请求
```bash
# 注册
curl -X POST http://localhost:8000/register -H "Content-Type: application/json" \
  -d '{"username":"player1","password":"password123"}'

# 登录获取 token
curl -X POST http://localhost:8000/login -H "Content-Type: application/json" \
  -d '{"username":"player1","password":"password123"}'

# 创建角色
curl -X POST http://localhost:8000/character/create \
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"name":"勇士"}'
```

连接 WebSocket 后即可输入指令体验游戏。

