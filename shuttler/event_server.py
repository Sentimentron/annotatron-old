import asyncio
import json
import websockets

async def event_loop(websocket, path):


async def message_handler(websocket, path):
    async for message in websocket:
        message = json.loads(message, encoding='utf8')
        if message["event"] == "authenticate":
            token = message["payload"]["token"]
        elif message["event"] == "remove

asyncio.get_event_loop().run_until_complete(

)
