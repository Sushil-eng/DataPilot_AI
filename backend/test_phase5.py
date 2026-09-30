import asyncio
import httpx

BASE_URL = "http://localhost:8000/api"

async def test_analytics():
    async with httpx.AsyncClient() as client:
        print("--- Testing /api/analytics/overview ---")
        res = await client.get(f"{BASE_URL}/analytics/overview")
        print("Overview Status:", res.status_code)
        print("Overview Response:", res.json())
        assert res.status_code == 200
        assert res.json()["success"] is True

        print("\n--- Testing /api/analytics/activity ---")
        res = await client.get(f"{BASE_URL}/analytics/activity?days=7")
        print("Activity Status:", res.status_code)
        print("Activity Response:", res.json())
        assert res.status_code == 200
        assert res.json()["success"] is True

        # Test listing datasets first to find a dataset ID if any
        res = await client.get(f"{BASE_URL}/datasets")
        datasets = res.json().get("data", {}).get("items", [])
        if datasets:
            dataset_id = datasets[0]["id"]
            print(f"\n--- Testing /api/analytics/datasets/{dataset_id} ---")
            res = await client.get(f"{BASE_URL}/analytics/datasets/{dataset_id}")
            print("Dataset Analytics Status:", res.status_code)
            print("Dataset Analytics Response:", res.json())
            assert res.status_code == 200
            assert res.json()["success"] is True
        else:
            print("\nNo datasets found in database to test per-dataset analytics.")

        print("\nAll Phase 5 Analytics tests passed!")

if __name__ == "__main__":
    asyncio.run(test_analytics())
