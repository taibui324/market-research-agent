import asyncio
import websockets
import json


async def listen():
    url = "ws://localhost:8000/research/ws/6db7376c-f50e-4007-9a33-3e42c67dc5f5"
    async with websockets.connect(url) as ws:
        print("Connected to WebSocket.")
        async for message in ws:
            data = json.loads(message)
            print("Update:", data)


asyncio.run(listen())
