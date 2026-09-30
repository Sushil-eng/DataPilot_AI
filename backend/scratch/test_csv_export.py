import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath('.'))

from app.database.connection import connect_to_mongo, get_db
from app.services.dataset_service import export_dataset

async def main():
    await connect_to_mongo()
    db = get_db()
    ds = await db.datasets.find_one()
    if not ds:
        print("No dataset found in database.")
        return
    res = await export_dataset(str(ds['_id']))
    if not res:
        print("Export returned None.")
        return
    content_bytes, filename, media_type = res
    print(f"Export Success: filename='{filename}' media_type='{media_type}' bytes={len(content_bytes)}")
    print("--- CSV Header & First 2 Rows ---")
    text = content_bytes.decode('utf-8-sig')
    lines = text.splitlines()
    for l in lines[:5]:
        print(l)

if __name__ == '__main__':
    asyncio.run(main())
