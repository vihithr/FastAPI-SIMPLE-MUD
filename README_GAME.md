# MUD RPG 游戏

基于 FastAPI 的多人在线文字 RPG 游戏（MUD风格）。

## 功能特性

- ✅ 用户注册和登录（JWT认证）
- ✅ 角色创建和管理
- ✅ 多人实时在线（WebSocket）
- ✅ 文字冒险系统（房间探索、移动）
- ✅ 回合制战斗系统
- ✅ 物品和装备系统
- ✅ 经验值和升级系统

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行应用

```bash
cd app
python main.py
```

或者使用 uvicorn：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 访问API文档

打开浏览器访问：http://localhost:8000/docs

## API端点

### REST API

- `POST /register` - 用户注册
  ```json
  {
    "username": "player1",
    "password": "password123"
  }
  ```

- `POST /login` - 用户登录
  ```json
  {
    "username": "player1",
    "password": "password123"
  }
  ```
  返回JWT token

- `GET /character` - 获取角色信息（需要Bearer token）
- `POST /character/create` - 创建角色（需要Bearer token）
  ```json
  {
    "name": "勇士"
  }
  ```

### WebSocket

- `WS /ws?token=<jwt_token>` - 游戏连接

## 游戏命令

连接WebSocket后，发送JSON消息：

```json
{
  "action": "command",
  "data": "look"
}
```

### 可用命令

- **移动**: `north(n)`, `south(s)`, `east(e)`, `west(w)`
- **查看**: `look(l)` - 查看当前房间
- **属性**: `stats` - 查看角色属性
- **战斗**: `attack <目标名称>` - 攻击目标
- **物品**: 
  - `inventory(inv)` - 查看物品栏
  - `equip <物品名称>` - 装备物品
  - `unequip <槽位>` - 卸下装备
  - `use <物品名称>` - 使用物品
  - `equipment(eq)` - 查看当前装备
- **社交**: `say <消息>` - 在房间内说话
- **帮助**: `help` - 查看所有命令

## 游戏世界

游戏包含8个房间：
1. 新手村广场（起点）
2. 武器店
3. 魔法学院
4. 训练场
5. 黑暗森林入口
6. 森林深处
7. 神秘洞穴
8. 宝藏室

## 物品系统

### 武器
- 木剑（攻击+5）
- 铁剑（攻击+10）
- 魔法法杖（攻击+8, MP+20）

### 防具
- 布甲（防御+3）
- 皮甲（防御+6）
- 铁头盔（防御+4）

### 消耗品
- 治疗药水（恢复50HP）
- 魔法药水（恢复30MP）

## 战斗系统

- 回合制战斗
- 攻击力受装备影响
- 防御力减少受到的伤害
- 击败敌人获得经验值
- 经验值达到要求自动升级

## 使用示例

### 1. 注册用户

```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "player1", "password": "password123"}'
```

### 2. 登录获取token

```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "player1", "password": "password123"}'
```

### 3. 创建角色

```bash
curl -X POST "http://localhost:8000/character/create" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "勇士"}'
```

### 4. 连接WebSocket

使用WebSocket客户端（如Python的websockets库或浏览器JavaScript）连接：

```javascript
const ws = new WebSocket('ws://localhost:8000/ws?token=YOUR_TOKEN');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.message);
};

// 发送命令
ws.send(JSON.stringify({
  action: "command",
  data: "look"
}));
```

## 技术栈

- FastAPI - Web框架
- SQLAlchemy - ORM
- SQLite - 数据库
- WebSocket - 实时通信
- JWT - 身份认证
- Pydantic - 数据验证

## 数据库

数据库文件：`mud_game.db`（SQLite）

应用启动时会自动创建所有表和初始数据（房间、物品）。

## 注意事项

- 生产环境请修改 `auth.py` 中的 `SECRET_KEY`
- 建议使用环境变量管理敏感配置
- WebSocket连接需要有效的JWT token
- 每个用户只能创建一个角色

## 开发

项目结构：

```
app/
├── main.py              # FastAPI应用入口
├── database.py          # 数据库连接
├── models.py            # 数据模型
├── schemas.py           # Pydantic模型
├── auth.py              # 认证系统
├── game/                # 游戏逻辑
│   ├── world.py        # 游戏世界
│   ├── player.py       # 玩家系统
│   ├── combat.py       # 战斗系统
│   ├── items.py        # 物品系统
│   └── commands.py     # 命令处理
└── websocket/           # WebSocket管理
    └── manager.py      # 连接管理器
```

