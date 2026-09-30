# -*- coding: utf-8 -*-
"""
PHASE 2 — COMPREHENSIVE INTEGRATION TEST
==========================================
Tests ALL endpoints across 3 domains (Jobs, Companies, Products).
Includes error handling, security, and architecture verification.

Run: python test_phase2_final.py
"""
import sys
import asyncio

# Fix Windows encoding for Unicode output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database.connection import connect_to_mongo, close_mongo_connection

PASS = "✓"
FAIL = "✗"
results = {"passed": 0, "failed": 0, "errors": []}


def check(condition, name, detail=""):
    if condition:
        results["passed"] += 1
        print(f"  {PASS} {name}")
    else:
        results["failed"] += 1
        results["errors"].append(f"{name}: {detail}")
        print(f"  {FAIL} {name} — {detail}")


async def run_full_integration_test():
    print("=" * 70)
    print("DATAPILOT AI — PHASE 2 FINAL INTEGRATION TEST")
    print("=" * 70)

    await connect_to_mongo()

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:

            # ==================================================
            # 1. HEALTH CHECK
            # ==================================================
            print("\n── 1. HEALTH CHECK ──")
            r = await client.get("/api/health")
            check(r.status_code == 200, "GET /api/health returns 200")
            check(r.json()["data"]["status"] == "ok", "Health status is 'ok'")

            # ==================================================
            # 2. GENERIC DATA TEST — 3 DOMAINS
            # ==================================================

            # ── DOMAIN A: Jobs ──
            print("\n── 2A. DOMAIN: JOBS ──")
            job_task = await client.post("/api/tasks", json={
                "prompt": "Find Python developer jobs in Mumbai",
                "record_limit": 20
            })
            check(job_task.status_code == 200, "POST /api/tasks (Jobs)")
            job_task_id = job_task.json()["data"]["id"]
            check(job_task_id is not None, "Job Task ID returned")

            # Workflow auto-created
            job_wf = await client.get(f"/api/workflows/{job_task_id}")
            check(job_wf.status_code == 200, "GET /api/workflows/{task_id} (Jobs)")
            job_steps = job_wf.json()["data"]["steps"]
            check(len(job_steps) == 7, "7 generic workflow steps created for Jobs")
            check(job_steps[0]["name"] == "Understanding request", "Step 1: Understanding request")
            check(job_steps[6]["name"] == "Preparing dataset", "Step 7: Preparing dataset")
            check(all(s["status"] == "pending" for s in job_steps), "All steps initially pending")

            # Create dataset with job-specific schema
            job_ds = await client.post("/api/datasets", json={
                "task_id": job_task_id,
                "name": "Python Jobs Mumbai",
                "description": "Python developer positions in Mumbai",
                "schema": [
                    {"name": "job_title", "type": "string"},
                    {"name": "company", "type": "string"},
                    {"name": "salary", "type": "string"},
                    {"name": "posted_date", "type": "date"},
                    {"name": "apply_link", "type": "url"}
                ]
            })
            check(job_ds.status_code == 200, "POST /api/datasets (Job schema)")
            job_ds_id = job_ds.json()["data"]["id"]
            check(len(job_ds.json()["data"]["schema"]) == 5, "5 job-specific fields defined")

            # Add job records
            job_rec = await client.post(f"/api/datasets/{job_ds_id}/records", json={
                "job_title": "Senior Python Developer",
                "company": "TechCorp Mumbai",
                "salary": "15-22 LPA",
                "posted_date": "2026-09-25",
                "apply_link": "https://techcorp.com/apply/123"
            })
            check(job_rec.status_code == 200, "POST /api/datasets/{id}/records (Job record)")
            job_rec_id = job_rec.json()["data"]["id"]

            # Add source
            job_src = await client.post("/api/sources", json={
                "dataset_id": job_ds_id,
                "url": "https://naukri.com/python-jobs-mumbai",
                "title": "Naukri Job Listings",
                "source_type": "web"
            })
            check(job_src.status_code == 200, "POST /api/sources (Job source)")

            # ── DOMAIN B: Companies ──
            print("\n── 2B. DOMAIN: COMPANIES ──")
            company_task = await client.post("/api/tasks", json={
                "prompt": "Find AI startups in India",
                "record_limit": 50
            })
            check(company_task.status_code == 200, "POST /api/tasks (Companies)")
            company_task_id = company_task.json()["data"]["id"]

            company_wf = await client.get(f"/api/workflows/{company_task_id}")
            check(company_wf.status_code == 200, "Workflow auto-created for Companies")

            company_ds = await client.post("/api/datasets", json={
                "task_id": company_task_id,
                "name": "AI Startups India",
                "description": "AI/ML startups across Indian metros",
                "schema": [
                    {"name": "company_name", "type": "string"},
                    {"name": "domain", "type": "string"},
                    {"name": "funding_usd", "type": "number"},
                    {"name": "founded", "type": "date"},
                    {"name": "website", "type": "url"},
                    {"name": "is_profitable", "type": "boolean"}
                ]
            })
            check(company_ds.status_code == 200, "POST /api/datasets (Company schema)")
            company_ds_id = company_ds.json()["data"]["id"]
            check(len(company_ds.json()["data"]["schema"]) == 6, "6 company-specific fields (different from Jobs)")

            company_rec = await client.post(f"/api/datasets/{company_ds_id}/records", json={
                "company_name": "NeuralWave AI",
                "domain": "Computer Vision",
                "funding_usd": 2500000,
                "founded": "2023-03-15",
                "website": "https://neuralwave.ai",
                "is_profitable": False
            })
            check(company_rec.status_code == 200, "POST record (Company — different fields than Jobs)")
            company_rec_id = company_rec.json()["data"]["id"]

            company_src = await client.post("/api/sources", json={
                "dataset_id": company_ds_id,
                "url": "https://tracxn.com/explore/AI-Startups-in-India",
                "title": "Tracxn AI India",
                "source_type": "web"
            })
            check(company_src.status_code == 200, "POST /api/sources (Company source)")

            # ── DOMAIN C: Products ──
            print("\n── 2C. DOMAIN: PRODUCTS ──")
            product_task = await client.post("/api/tasks", json={
                "prompt": "Find laptops under ₹50,000",
                "record_limit": 30
            })
            check(product_task.status_code == 200, "POST /api/tasks (Products)")
            product_task_id = product_task.json()["data"]["id"]

            product_ds = await client.post("/api/datasets", json={
                "task_id": product_task_id,
                "name": "Budget Laptops",
                "description": "Laptops under ₹50,000 in Indian market",
                "schema": [
                    {"name": "product_name", "type": "string"},
                    {"name": "brand", "type": "string"},
                    {"name": "price_inr", "type": "number"},
                    {"name": "in_stock", "type": "boolean"},
                    {"name": "buy_link", "type": "url"}
                ]
            })
            check(product_ds.status_code == 200, "POST /api/datasets (Product schema)")
            product_ds_id = product_ds.json()["data"]["id"]

            product_rec = await client.post(f"/api/datasets/{product_ds_id}/records", json={
                "product_name": "ASUS VivoBook 15",
                "brand": "ASUS",
                "price_inr": 42990,
                "in_stock": True,
                "buy_link": "https://amazon.in/dp/B09EXAMPLE"
            })
            check(product_rec.status_code == 200, "POST record (Product — different fields)")
            product_rec_id = product_rec.json()["data"]["id"]

            product_src = await client.post("/api/sources", json={
                "dataset_id": product_ds_id,
                "url": "https://amazon.in/laptops-under-50000",
                "title": "Amazon India Laptops",
                "source_type": "web"
            })
            check(product_src.status_code == 200, "POST /api/sources (Product source)")

            # ==================================================
            # 3. VERIFY SAME API, DIFFERENT SCHEMAS
            # ==================================================
            print("\n── 3. CROSS-DOMAIN VERIFICATION ──")

            # Same Task API across domains
            all_tasks = await client.get("/api/tasks?limit=50")
            check(all_tasks.status_code == 200, "GET /api/tasks returns all domain tasks")
            task_items = all_tasks.json()["data"]["items"]
            check(len(task_items) >= 3, f"At least 3 tasks from 3 domains (got {len(task_items)})")

            # Same Dataset API across domains
            all_datasets = await client.get("/api/datasets?limit=50")
            check(all_datasets.status_code == 200, "GET /api/datasets returns all domain datasets")

            # Verify different schemas work
            job_ds_detail = await client.get(f"/api/datasets/{job_ds_id}")
            company_ds_detail = await client.get(f"/api/datasets/{company_ds_id}")
            product_ds_detail = await client.get(f"/api/datasets/{product_ds_id}")

            job_fields = set(f["name"] for f in job_ds_detail.json()["data"]["schema"])
            company_fields = set(f["name"] for f in company_ds_detail.json()["data"]["schema"])
            product_fields = set(f["name"] for f in product_ds_detail.json()["data"]["schema"])

            check(job_fields != company_fields, "Job and Company schemas are different")
            check(company_fields != product_fields, "Company and Product schemas are different")
            check(job_fields != product_fields, "Job and Product schemas are different")

            # Verify records are stored with correct data
            job_recs = await client.get(f"/api/datasets/{job_ds_id}/records")
            check(job_recs.status_code == 200, "GET job records")
            check(job_recs.json()["data"]["items"][0]["data"].get("job_title") is not None, "Job record has job_title field")

            company_recs = await client.get(f"/api/datasets/{company_ds_id}/records")
            check(company_recs.status_code == 200, "GET company records")
            check(company_recs.json()["data"]["items"][0]["data"].get("company_name") is not None, "Company record has company_name field")

            product_recs = await client.get(f"/api/datasets/{product_ds_id}/records")
            check(product_recs.status_code == 200, "GET product records")
            check(product_recs.json()["data"]["items"][0]["data"].get("product_name") is not None, "Product record has product_name field")

            # Sources work across all datasets
            for ds_id, domain in [(job_ds_id, "Jobs"), (company_ds_id, "Companies"), (product_ds_id, "Products")]:
                src_res = await client.get(f"/api/sources/{ds_id}")
                check(src_res.status_code == 200, f"GET /api/sources for {domain}")
                check(src_res.json()["data"]["count"] >= 1, f"At least 1 source for {domain}")

            # ==================================================
            # 4. WORKFLOW API VERIFICATION
            # ==================================================
            print("\n── 4. WORKFLOW API ──")

            # PATCH workflow
            wf_patch = await client.patch(f"/api/workflows/{job_task_id}", json={
                "status": "running", "progress": 15
            })
            check(wf_patch.status_code == 200, "PATCH /api/workflows/{task_id}")
            check(wf_patch.json()["data"]["status"] == "running", "Workflow status updated to running")

            # GET steps
            steps_res = await client.get(f"/api/workflows/{job_task_id}/steps")
            check(steps_res.status_code == 200, "GET /api/workflows/{task_id}/steps")
            check(len(steps_res.json()["data"]["steps"]) == 7, "7 steps returned")

            # PATCH step
            step_patch = await client.patch(f"/api/workflows/{job_task_id}/steps/step_1", json={
                "status": "completed",
                "result": {"summary": "Understood: Find Python developer jobs in Mumbai"}
            })
            check(step_patch.status_code == 200, "PATCH /api/workflows/{task_id}/steps/{step_id}")
            check(step_patch.json()["data"]["status"] == "completed", "Step status updated")

            # Verify progress recalculated
            wf_after = await client.get(f"/api/workflows/{job_task_id}")
            check(wf_after.json()["data"]["progress"] == 14, "Progress auto-calculated (1/7 = 14%)")

            # Complete all steps
            for i in range(2, 8):
                await client.patch(f"/api/workflows/{job_task_id}/steps/step_{i}", json={
                    "status": "completed"
                })
            wf_complete = await client.get(f"/api/workflows/{job_task_id}")
            check(wf_complete.json()["data"]["progress"] == 100, "100% after all steps completed")
            check(wf_complete.json()["data"]["status"] == "completed", "Workflow status auto-set to completed")

            # Task status synced
            task_synced = await client.get(f"/api/tasks/{job_task_id}")
            check(task_synced.json()["data"]["status"] == "completed", "Task status synced with workflow")

            # ==================================================
            # 5. RECORD CRUD
            # ==================================================
            print("\n── 5. RECORD CRUD ──")

            # PATCH record
            rec_patch = await client.patch(f"/api/datasets/{job_ds_id}/records/{job_rec_id}", json={
                "salary": "18-25 LPA"
            })
            check(rec_patch.status_code == 200, "PATCH /api/datasets/{id}/records/{id}")
            check(rec_patch.json()["data"]["data"]["salary"] == "18-25 LPA", "Record field updated")
            check(rec_patch.json()["data"]["data"]["job_title"] == "Senior Python Developer", "Other fields preserved")

            # DELETE record
            rec_del = await client.delete(f"/api/datasets/{product_ds_id}/records/{product_rec_id}")
            check(rec_del.status_code == 200, "DELETE /api/datasets/{id}/records/{id}")

            # Verify count decremented
            ds_after_del = await client.get(f"/api/datasets/{product_ds_id}")
            # The count should reflect auto-created records minus 1 plus the one we added minus 1
            # Auto-created has 0 records (this was a new dataset), we added 1 then deleted 1 = 0
            check(ds_after_del.json()["data"]["record_count"] == 0, "Record count decremented after delete")

            # ==================================================
            # 6. ERROR TESTING
            # ==================================================
            print("\n── 6. ERROR TESTING ──")

            # Empty prompt
            empty_prompt = await client.post("/api/tasks", json={"prompt": "", "record_limit": 10})
            check(empty_prompt.status_code == 422, "Empty prompt rejected (422)")

            # Invalid task ID
            bad_task = await client.get("/api/tasks/invalid_id_123")
            check(bad_task.status_code in (400, 404), "Invalid task ID returns 400/404")

            # Non-existent valid ObjectId
            fake_id = "000000000000000000000000"
            fake_task = await client.get(f"/api/tasks/{fake_id}")
            check(fake_task.status_code == 404, "Non-existent task returns 404")

            # Invalid dataset ID
            bad_ds = await client.get("/api/datasets/not_a_valid_id")
            check(bad_ds.status_code in (400, 404), "Invalid dataset ID returns 400/404")

            # Invalid record ID
            bad_rec = await client.get(f"/api/datasets/{job_ds_id}/records")
            check(bad_rec.status_code == 200, "GET records for valid dataset succeeds")

            bad_rec_patch = await client.patch(f"/api/datasets/{job_ds_id}/records/{fake_id}", json={"x": 1})
            check(bad_rec_patch.status_code == 404, "Non-existent record returns 404")

            # Invalid schema type
            bad_schema = await client.post("/api/datasets", json={
                "name": "Invalid Schema",
                "schema": [{"name": "x", "type": "xml"}]
            })
            check(bad_schema.status_code in (400, 422), "Invalid schema type rejected")

            # Invalid workflow status
            bad_status = await client.patch(f"/api/workflows/{company_task_id}", json={
                "status": "exploded"
            })
            check(bad_status.status_code == 400, "Invalid workflow status rejected")

            # Invalid step ID
            bad_step = await client.patch(f"/api/workflows/{company_task_id}/steps/step_99", json={
                "status": "completed"
            })
            check(bad_step.status_code == 404, "Invalid step ID returns 404")

            # Empty update body
            empty_update = await client.patch(f"/api/tasks/{company_task_id}", json={})
            check(empty_update.status_code in (400, 404), "Empty update body handled")

            # Non-existent workflow
            no_wf = await client.get(f"/api/workflows/{fake_id}")
            check(no_wf.status_code == 404, "Non-existent workflow returns 404")

            # ==================================================
            # 7. DATASET PATCH & DELETE
            # ==================================================
            print("\n── 7. DATASET PATCH & DELETE ──")

            ds_patch = await client.patch(f"/api/datasets/{company_ds_id}", json={
                "name": "AI Startups India v2",
                "description": "Updated description"
            })
            check(ds_patch.status_code == 200, "PATCH /api/datasets/{id}")
            check(ds_patch.json()["data"]["name"] == "AI Startups India v2", "Dataset name updated")

            # Delete dataset
            ds_del = await client.delete(f"/api/datasets/{product_ds_id}")
            check(ds_del.status_code == 200, "DELETE /api/datasets/{id}")

            # Confirm deleted
            ds_gone = await client.get(f"/api/datasets/{product_ds_id}")
            check(ds_gone.status_code == 404, "Deleted dataset returns 404")

            # ==================================================
            # 8. TASK DELETE (CASCADE)
            # ==================================================
            print("\n── 8. TASK CASCADE DELETE ──")

            del_task = await client.delete(f"/api/tasks/{product_task_id}")
            check(del_task.status_code == 200, "DELETE /api/tasks/{id} (cascade)")

            # Verify cascade: workflow gone
            wf_gone = await client.get(f"/api/workflows/{product_task_id}")
            check(wf_gone.status_code == 404, "Workflow cascade deleted with task")

            # ==================================================
            # 9. TASK LIST WITH FILTERS
            # ==================================================
            print("\n── 9. TASK LIST FILTERS ──")

            search_res = await client.get("/api/tasks?search=Python")
            check(search_res.status_code == 200, "GET /api/tasks?search=Python")
            check(len(search_res.json()["data"]["items"]) >= 1, "Search by prompt works")

            status_res = await client.get("/api/tasks?status=completed")
            check(status_res.status_code == 200, "GET /api/tasks?status=completed")

            page_res = await client.get("/api/tasks?page=1&limit=2")
            check(page_res.status_code == 200, "Pagination works (page=1, limit=2)")
            check(len(page_res.json()["data"]["items"]) <= 2, "Pagination limits results")

            # ==================================================
            # 10. API RESPONSE FORMAT
            # ==================================================
            print("\n── 10. API RESPONSE FORMAT ──")

            health_res = await client.get("/api/health")
            check("success" in health_res.json(), "Responses have 'success' key")
            check("data" in health_res.json(), "Responses have 'data' key")

            # Error response format
            err_res = await client.get(f"/api/tasks/{fake_id}")
            err_detail = err_res.json().get("detail", {})
            check(isinstance(err_detail, dict), "Error response is structured")
            check("error" in err_detail, "Error has 'error' key")
            check("message" in err_detail.get("error", {}), "Error has 'message' field")

            # ==================================================
            # 11. DATASET LIST WITH FILTERS
            # ==================================================
            print("\n── 11. DATASET FILTERS ──")

            ds_search = await client.get("/api/datasets?search=Jobs")
            check(ds_search.status_code == 200, "GET /api/datasets?search=Jobs")

            ds_by_task = await client.get(f"/api/datasets?task_id={job_task_id}")
            check(ds_by_task.status_code == 200, "GET /api/datasets?task_id=...")
            # At least the auto-created one + the one we created
            check(len(ds_by_task.json()["data"]["items"]) >= 1, "Task-filtered datasets returned")

            # ==================================================
            # SUMMARY
            # ==================================================
            print("\n" + "=" * 70)
            total = results["passed"] + results["failed"]
            print(f"RESULTS: {results['passed']}/{total} passed, {results['failed']} failed")
            print("=" * 70)

            if results["failed"] > 0:
                print("\nFAILED TESTS:")
                for e in results["errors"]:
                    print(f"  {FAIL} {e}")
            else:
                print("\n🎉 ALL PHASE 2 INTEGRATION TESTS PASSED!")

            print("=" * 70)
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(run_full_integration_test())
