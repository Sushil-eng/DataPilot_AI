import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database.connection import connect_to_mongo, close_mongo_connection

def log(msg=""):
    print(msg, flush=True)

async def run_tests():
    log("=== STARTING PHASE 2 API TESTS ===")
    await connect_to_mongo()

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # 1. TASK & WORKFLOW CREATION
            log("\n--- 1. Testing Task & Generic Workflow Creation ---")
            task_res = await client.post("/api/tasks", json={
                "prompt": "Research tech companies and developer jobs in Mumbai",
                "record_limit": 20
            })
            assert task_res.status_code == 200, f"Task creation failed: {task_res.text}"
            task_data = task_res.json()["data"]
            task_id = task_data["id"]
            log(f"Task created with ID: {task_id}")

            # GET Workflow
            wf_res = await client.get(f"/api/workflows/{task_id}")
            assert wf_res.status_code == 200, f"Get workflow failed: {wf_res.text}"
            wf_data = wf_res.json()["data"]
            assert wf_data["task_id"] == task_id
            assert wf_data["status"] == "pending"
            steps = wf_data["steps"]
            assert len(steps) == 7, f"Expected 7 generic steps, got {len(steps)}"
            log(f"Workflow retrieved with {len(steps)} generic steps:")
            for idx, s in enumerate(steps, 1):
                log(f"  Step {idx}: {s['name']} (status: {s['status']})")
            assert steps[0]["name"] == "Understanding request"
            assert steps[6]["name"] == "Preparing dataset"

            # PATCH Workflow Status
            wf_patch_res = await client.patch(f"/api/workflows/{task_id}", json={
                "status": "running",
                "progress": 10
            })
            assert wf_patch_res.status_code == 200, f"Patch workflow failed: {wf_patch_res.text}"
            assert wf_patch_res.json()["data"]["status"] == "running"
            log("Workflow status patched to 'running'")

            # GET Workflow Steps
            steps_res = await client.get(f"/api/workflows/{task_id}/steps")
            assert steps_res.status_code == 200
            assert len(steps_res.json()["data"]["steps"]) == 7

            # PATCH Workflow Step
            step_patch_res = await client.patch(f"/api/workflows/{task_id}/steps/step_1", json={
                "status": "completed",
                "result": {"summary": "Parsed user prompt successfully"}
            })
            assert step_patch_res.status_code == 200, f"Step patch failed: {step_patch_res.text}"
            step_updated = step_patch_res.json()["data"]
            assert step_updated["status"] == "completed"
            log("Step 1 ('Understanding request') patched to 'completed'")

            # Check calculated progress on workflow
            wf_check = (await client.get(f"/api/workflows/{task_id}")).json()["data"]
            log(f"Updated Workflow Progress: {wf_check['progress']}%")

            # 2. DATASETS FOR 3 DOMAINS (Company, Product, Job)
            log("\n--- 2. Testing Datasets across 3 Domains ---")

            # Domain A: Company Research
            log("\n[Domain A: Company Research]")
            company_ds_res = await client.post("/api/datasets", json={
                "task_id": task_id,
                "name": "Company Directory",
                "description": "Directory of tech companies in Mumbai",
                "schema": [
                    {"name": "company", "type": "string"},
                    {"name": "location", "type": "string"},
                    {"name": "website", "type": "url"}
                ]
            })
            assert company_ds_res.status_code == 200, f"Company DS create failed: {company_ds_res.text}"
            company_ds_id = company_ds_res.json()["data"]["id"]
            log(f"Company Dataset created with ID: {company_ds_id}")

            # Add Company Record
            rec1_res = await client.post(f"/api/datasets/{company_ds_id}/records", json={
                "company": "ABC Tech",
                "location": "Mumbai",
                "website": "https://abctech.example.com"
            })
            assert rec1_res.status_code == 200, f"Company record insert failed: {rec1_res.text}"
            rec1_id = rec1_res.json()["data"]["id"]
            log(f"Company record added: {rec1_res.json()['data']['data']}")

            # Add Source for Company Dataset
            src1_res = await client.post("/api/sources", json={
                "dataset_id": company_ds_id,
                "url": "https://abctech.example.com/about",
                "title": "ABC Tech Official Website",
                "source_type": "web"
            })
            assert src1_res.status_code == 200, f"Company source insert failed: {src1_res.text}"
            log(f"Company source added: {src1_res.json()['data']['title']}")

            # Domain B: Product Research
            log("\n[Domain B: Product Research]")
            prod_ds_res = await client.post("/api/datasets", json={
                "task_id": task_id,
                "name": "Smartphone Specs",
                "description": "Comparison of mobile phones",
                "schema": [
                    {"name": "product", "type": "string"},
                    {"name": "price", "type": "number"},
                    {"name": "in_stock", "type": "boolean"}
                ]
            })
            assert prod_ds_res.status_code == 200, f"Product DS create failed: {prod_ds_res.text}"
            prod_ds_id = prod_ds_res.json()["data"]["id"]
            log(f"Product Dataset created with ID: {prod_ds_id}")

            # Add Product Record
            rec2_res = await client.post(f"/api/datasets/{prod_ds_id}/records", json={
                "product": "Laptop",
                "price": 50000,
                "in_stock": True
            })
            assert rec2_res.status_code == 200, f"Product record insert failed: {rec2_res.text}"
            rec2_id = rec2_res.json()["data"]["id"]
            log(f"Product record added: {rec2_res.json()['data']['data']}")

            # Add Source for Product Dataset
            src2_res = await client.post("/api/sources", json={
                "dataset_id": prod_ds_id,
                "url": "https://e-store.example.com/laptops",
                "title": "E-Store Product Listing",
                "source_type": "web"
            })
            assert src2_res.status_code == 200, f"Product source insert failed: {src2_res.text}"
            log(f"Product source added: {src2_res.json()['data']['title']}")

            # Domain C: Job Research
            log("\n[Domain C: Job Research]")
            job_ds_res = await client.post("/api/datasets", json={
                "task_id": task_id,
                "name": "Developer Job Listings",
                "description": "Tech job openings",
                "schema": [
                    {"name": "job_title", "type": "string"},
                    {"name": "salary", "type": "string"},
                    {"name": "posted_date", "type": "date"}
                ]
            })
            assert job_ds_res.status_code == 200, f"Job DS create failed: {job_ds_res.text}"
            job_ds_id = job_ds_res.json()["data"]["id"]
            log(f"Job Dataset created with ID: {job_ds_id}")

            # Add Job Record
            rec3_res = await client.post(f"/api/datasets/{job_ds_id}/records", json={
                "job_title": "Developer",
                "salary": "10 LPA",
                "posted_date": "2026-09-28"
            })
            assert rec3_res.status_code == 200, f"Job record insert failed: {rec3_res.text}"
            rec3_id = rec3_res.json()["data"]["id"]
            log(f"Job record added: {rec3_res.json()['data']['data']}")

            # Add Source for Job Dataset
            src3_res = await client.post("/api/sources", json={
                "dataset_id": job_ds_id,
                "url": "https://jobs.example.com/api/v1/jobs",
                "title": "Jobs API Endpoint",
                "source_type": "api"
            })
            assert src3_res.status_code == 200, f"Job source insert failed: {src3_res.text}"
            log(f"Job source added: {src3_res.json()['data']['title']}")

            # 3. VERIFYING SOURCES ENDPOINT
            log("\n--- 3. Testing Sources Retrieval ---")
            get_src_res = await client.get(f"/api/sources/{company_ds_id}")
            assert get_src_res.status_code == 200
            sources_list = get_src_res.json()["data"]["items"]
            assert len(sources_list) == 1
            log(f"Retrieved {len(sources_list)} source for Company Dataset: {sources_list[0]['url']}")

            # 4. TESTING RECORD PATCH & DELETE
            log("\n--- 4. Testing Record Patch & Delete ---")
            patch_rec_res = await client.patch(f"/api/datasets/{company_ds_id}/records/{rec1_id}", json={
                "location": "Mumbai Central"
            })
            assert patch_rec_res.status_code == 200
            log(f"Patched record location: {patch_rec_res.json()['data']['data']}")

            del_rec_res = await client.delete(f"/api/datasets/{job_ds_id}/records/{rec3_id}")
            assert del_rec_res.status_code == 200
            log("Deleted job record successfully")

            # 5. TESTING SCHEMA TYPE VALIDATION
            log("\n--- 5. Testing Schema Type Validation ---")
            invalid_schema_res = await client.post("/api/datasets", json={
                "name": "Invalid Schema Dataset",
                "schema": [{"name": "invalid_field", "type": "unsupported_type"}]
            })
            assert invalid_schema_res.status_code in (400, 422), f"Expected 400 or 422, got {invalid_schema_res.status_code}"
            error_detail = invalid_schema_res.json().get("detail", {})
            if isinstance(error_detail, list):
                error_msg = error_detail[0].get("msg", "Validation error")
            elif isinstance(error_detail, dict):
                error_msg = error_detail.get("error", {}).get("message", "Validation error")
            else:
                error_msg = str(error_detail)
            log(f"Invalid schema correctly rejected with {invalid_schema_res.status_code}: {error_msg}")

            # 6. TESTING DATASET DELETE
            log("\n--- 6. Testing Dataset Delete Cleanup ---")
            del_ds_res = await client.delete(f"/api/datasets/{prod_ds_id}")
            assert del_ds_res.status_code == 200
            log("Product dataset deleted successfully")

            # Verify dataset is deleted
            get_del_ds = await client.get(f"/api/datasets/{prod_ds_id}")
            assert get_del_ds.status_code == 404

            log("\n==================================================")
            log("ALL PHASE 2 API TESTS PASSED SUCCESSFULLY!")
            log("==================================================")
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(run_tests())
