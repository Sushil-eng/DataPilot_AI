"""Quick script to drop the datapilot database and re-seed."""
import asyncio
from app.database.connection import connect_to_mongo, close_mongo_connection, get_db

async def main():
    await connect_to_mongo()
    db = get_db()
    # Drop all collections
    for coll_name in ["tasks", "workflows", "datasets", "dataset_records", "sources"]:
        await db[coll_name].drop()
        print(f"Dropped: {coll_name}")
    print("All collections dropped.")
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(main())
