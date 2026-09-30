import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000/api"

async def test_dataset_export_and_features():
    async with httpx.AsyncClient() as client:
        print("--- 1. Testing Dataset Creation for Multiple Domains ---")
        
        # Create Job Dataset
        res_job = await client.post(f"{BASE_URL}/datasets", json={
            "name": "Software Engineering Jobs Dataset",
            "description": "Scraped tech jobs",
            "schema_fields": [
                {"name": "job_title", "type": "string"},
                {"name": "company", "type": "string"},
                {"name": "salary_min", "type": "number"},
                {"name": "location", "type": "string"}
            ]
        })
        print("Job Dataset Creation Status:", res_job.status_code)
        assert res_job.status_code == 200
        job_dataset_id = res_job.json()["data"]["id"]

        # Insert records into Job Dataset
        await client.post(f"{BASE_URL}/datasets/{job_dataset_id}/records", json={
            "job_title": "Senior Python Developer",
            "company": "Tech Corp",
            "salary_min": 120000,
            "location": "Remote",
            "source_url": "https://example.com/jobs/1"
        })
        await client.post(f"{BASE_URL}/datasets/{job_dataset_id}/records", json={
            "job_title": "Frontend Engineer",
            "company": "Design Inc",
            "salary_min": 95000,
            "location": "New York",
            "source_url": "https://example.com/jobs/2"
        })

        # Create Product Dataset
        res_prod = await client.post(f"{BASE_URL}/datasets", json={
            "name": "E-Commerce Products Dataset",
            "description": "Scraped product listings",
            "schema_fields": [
                {"name": "product_name", "type": "string"},
                {"name": "category", "type": "string"},
                {"name": "price", "type": "number"},
                {"name": "rating", "type": "number"}
            ]
        })
        assert res_prod.status_code == 200
        prod_dataset_id = res_prod.json()["data"]["id"]

        await client.post(f"{BASE_URL}/datasets/{prod_dataset_id}/records", json={
            "product_name": "Wireless Noise Canceling Headphones",
            "category": "Electronics",
            "price": 299.99,
            "rating": 4.8
        })

        print("Created Datasets & Records successfully.")

        print("\n--- 2. Testing Records Search & Pagination ---")
        all_recs = await client.get(f"{BASE_URL}/datasets/{job_dataset_id}/records")
        print("All Records:", all_recs.json())
        search_res = await client.get(f"{BASE_URL}/datasets/{job_dataset_id}/records?search=Python")
        print("Search Response Status:", search_res.status_code)
        search_data = search_res.json()["data"]
        print(f"Found {search_data['total']} matching record(s) for query 'Python'")
        assert search_res.status_code == 200
        assert search_data["total"] >= 1

        print("\n--- 3. Testing CSV Export Endpoint ---")
        csv_res = await client.get(f"{BASE_URL}/datasets/{job_dataset_id}/export?format=csv")
        print("CSV Export Status:", csv_res.status_code)
        print("Content-Disposition Header:", csv_res.headers.get("content-disposition"))
        csv_content = csv_res.text
        print("CSV Content Preview:\n", csv_content)
        assert csv_res.status_code == 200
        assert "job_title,company,salary_min,location" in csv_content
        assert "Senior Python Developer" in csv_content

        print("\n--- 4. Testing JSON Export Endpoint ---")
        json_res = await client.get(f"{BASE_URL}/datasets/{job_dataset_id}/export?format=json")
        print("JSON Export Status:", json_res.status_code)
        json_records = json_res.json()
        print(f"Exported {len(json_records)} JSON record(s). Preview first record:")
        print(json.dumps(json_records[0], indent=2))
        assert json_res.status_code == 200
        assert isinstance(json_records, list)
        assert json_records[0]["job_title"] is not None

        # Clean up test datasets
        await client.delete(f"{BASE_URL}/datasets/{job_dataset_id}")
        await client.delete(f"{BASE_URL}/datasets/{prod_dataset_id}")

        print("\nAll Phase 5 Prompt 2 Dataset Export & Features tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(test_dataset_export_and_features())
