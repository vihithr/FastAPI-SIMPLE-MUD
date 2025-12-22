"""
简单的WebSocket测试客户端示例
用于测试MUD RPG游戏
"""
import asyncio
import websockets
import json
import sys


async def game_client(token: str, uri: str = "ws://localhost:8000/ws"):
    """游戏客户端"""
    async with websockets.connect(f"{uri}?token={token}") as websocket:
        print("已连接到游戏服务器！")
        print("输入命令开始游戏，输入 'quit' 退出\n")
        
        async def receive_messages():
            """接收服务器消息"""
            try:
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    print(f"[{data.get('type', 'info').upper()}] {data.get('message', '')}")
                    if data.get('data'):
                        print(f"数据: {data['data']}")
                    print()  # 空行
            except websockets.exceptions.ConnectionClosed:
                print("\n连接已断开")
        
        async def send_commands():
            """发送命令"""
            try:
                while True:
                    command = await asyncio.get_event_loop().run_in_executor(
                        None, input, "> "
                    )
                    if command.strip().lower() == 'quit':
                        await websocket.close()
                        break
                    
                    if command.strip():
                        message = {
                            "action": "command",
                            "data": command.strip()
                        }
                        await websocket.send(json.dumps(message))
            except EOFError:
                pass
        
        # 同时运行接收和发送
        await asyncio.gather(
            receive_messages(),
            send_commands()
        )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python test_client.py <jwt_token>")
        print("\n获取token:")
        print("1. 注册用户: POST http://localhost:8000/register")
        print("   {\"username\": \"test\", \"password\": \"test123\"}")
        print("2. 登录获取token: POST http://localhost:8000/login")
        print("   {\"username\": \"test\", \"password\": \"test123\"}")
        print("3. 创建角色: POST http://localhost:8000/character/create")
        print("   {\"name\": \"勇士\"}")
        sys.exit(1)
    
    token = sys.argv[1]
    asyncio.run(game_client(token))

