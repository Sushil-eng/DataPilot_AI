import asyncio
import certifi
from motor.motor_asyncio import AsyncIOMotorClient

URI = "mongodb+srv://abhishekin420_db_user:DataPilot2026Test@datapilotai.l45ysep.mongodb.net/?appName=DataPilotAI"

async def test():
    print(f"Testing connection to Atlas...")
    try:
        client = AsyncIOMotorClient(
            URI,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=10000
        )
        result = await client.admin.command('ping')
        print(f"SUCCESS: {result}")
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

asyncio.run(test())
