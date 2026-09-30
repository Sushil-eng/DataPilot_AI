import urllib.request
import urllib.parse
import json
import time
import sys

BASE_URL = "http://localhost:8000/api"

def log(msg=""):
    print(msg, flush=True)

def request(method, path, data=None):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method=method)
    if data is not None:
        payload = json.dumps(data).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    else:
        payload = None
    try:
        with urllib.request.urlopen(req, data=payload) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"error": body}

def main():
    log("=== STARTING PHASE 2 HTTP API TESTS ===")
    
    # 1. TASK & WORKFLOW CREATION
    log("\n--- 1. Testing Task & Generic Workflow Creation ---")
    status, res = request("POST", "/tasks", {
        "prompt": "Research tech companies, products, and developer jobs in Mumbai",
        "record_limit": 20
    })
    assert status == 200, f"Task creation failed: {res}"
    task_id = res["data"]["id"]
    log(f"Task created with ID: {task_id}")

    # GET Workflow
    status, res = request("GET", f"/workflows/{task_id}")
    assert status == 200, f"Get workflow failed: {res}"
    wf_data = res["data"]
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
    status, res = request("PATCH", f"/workflows/{task_id}", {
        "status": "running",
        "progress": 10
    })
    assert status == 200, f"Patch workflow status failed: {res}"
    assert res["data"]["status"] == "running"
    log("Workflow status patched to 'running'")

    # GET Workflow Steps
    status, res = request("GET", f"/workflows/{task_id}/steps")
    assert status == 200
    assert len(res["data"]["steps"]) == 7

    # PATCH Workflow Step
    status, res = request("PATCH", f"/workflows/{task_id}/steps/step_1", {
        "status": "completed",
        "result": {"summary": "Parsed user prompt successfully"}
    })
    assert status == 200, f"Step patch failed: {res}"
    assert res["data"]["status"] == "completed"
    log("Step 1 ('Understanding request') patched to 'completed'")

    # Check Workflow Progress recalculated
    status, res = request("GET", f"/workflows/{task_id}")
    log(f"Updated Workflow Progress: {res['data']['progress']}%")

    # 2. DATASETS FOR 3 DOMAINS (Company, Product, Job)
    log("\n--- 2. Testing Datasets across 3 Domains ---")

    # Domain A: Company Research
    log("\n[Domain A: Company Research]")
    status, res = request("POST", "/datasets", {
        "task_id": task_id,
        "name": "Company Directory",
        "description": "Directory of tech companies in Mumbai",
        "schema": [
            {"name": "company", "type": "string"},
            {"name": "location", "type": "string"},
            {"name": "website", "type": "url"}
        ]
    })
    assert status == 200, f"Company DS create failed: {res}"
    company_ds_id = res["data"]["id"]
    log(f"Company Dataset created with ID: {company_ds_id}")

    # Add Company Record
    status, res = request("POST", f"/datasets/{company_ds_id}/records", {
        "company": "ABC Tech",
        "location": "Mumbai",
        "website": "https://abctech.example.com"
    })
    assert status == 200, f"Company record insert failed: {res}"
    rec1_id = res["data"]["id"]
    log(f"Company record added: {res['data']['data']}")

    # Add Source for Company Dataset
    status, res = request("POST", "/sources", {
        "dataset_id": company_ds_id,
        "url": "https://abctech.example.com/about",
        "title": "ABC Tech Official Website",
        "source_type": "web"
    })
    assert status == 200, f"Company source insert failed: {res}"
    log(f"Company source added: {res['data']['title']}")

    # Domain B: Product Research
    log("\n[Domain B: Product Research]")
    status, res = request("POST", "/datasets", {
        "task_id": task_id,
        "name": "Smartphone Specs",
        "description": "Comparison of mobile phones",
        "schema": [
            {"name": "product", "type": "string"},
            {"name": "price", "type": "number"},
            {"name": "in_stock", "type": "boolean"}
        ]
    })
    assert status == 200, f"Product DS create failed: {res}"
    prod_ds_id = res["data"]["id"]
    log(f"Product Dataset created with ID: {prod_ds_id}")

    # Add Product Record
    status, res = request("POST", f"/datasets/{prod_ds_id}/records", {
        "product": "Laptop",
        "price": 50000,
        "in_stock": True
    })
    assert status == 200, f"Product record insert failed: {res}"
    rec2_id = res["data"]["id"]
    log(f"Product record added: {res['data']['data']}")

    # Add Source for Product Dataset
    status, res = request("POST", "/sources", {
        "dataset_id": prod_ds_id,
        "url": "https://e-store.example.com/laptops",
        "title": "E-Store Product Listing",
        "source_type": "web"
    })
    assert status == 200, f"Product source insert failed: {res}"
    log(f"Product source added: {res['data']['title']}")

    # Domain C: Job Research
    log("\n[Domain C: Job Research]")
    status, res = request("POST", "/datasets", {
        "task_id": task_id,
        "name": "Developer Job Listings",
        "description": "Tech job openings",
        "schema": [
            {"name": "job_title", "type": "string"},
            {"name": "salary", "type": "string"},
            {"name": "posted_date", "type": "date"}
        ]
    })
    assert status == 200, f"Job DS create failed: {res}"
    job_ds_id = res["data"]["id"]
    log(f"Job Dataset created with ID: {job_ds_id}")

    # Add Job Record
    status, res = request("POST", f"/datasets/{job_ds_id}/records", {
        "job_title": "Developer",
        "salary": "10 LPA",
        "posted_date": "2026-09-28"
    })
    assert status == 200, f"Job record insert failed: {res}"
    rec3_id = res["data"]["id"]
    log(f"Job record added: {res['data']['data']}")

    # Add Source for Job Dataset
    status, res = request("POST", "/sources", {
        "dataset_id": job_ds_id,
        "url": "https://jobs.example.com/api/v1/jobs",
        "title": "Jobs API Endpoint",
        "source_type": "api"
    })
    assert status == 200, f"Job source insert failed: {res}"
    log(f"Job source added: {res['data']['title']}")

    # 3. VERIFYING SOURCES ENDPOINT
    log("\n--- 3. Testing Sources Retrieval ---")
    status, res = request("GET", f"/sources/{company_ds_id}")
    assert status == 200
    sources_list = res["data"]["items"]
    assert len(sources_list) == 1
    log(f"Retrieved {len(sources_list)} source for Company Dataset: {sources_list[0]['url']}")

    # 4. TESTING RECORD PATCH & DELETE
    log("\n--- 4. Testing Record Patch & Delete ---")
    status, res = request("PATCH", f"/datasets/{company_ds_id}/records/{rec1_id}", {
        "location": "Mumbai Central"
    })
    assert status == 200
    log(f"Patched record location: {res['data']['data']}")

    status, res = request("DELETE", f"/datasets/{job_ds_id}/records/{rec3_id}")
    assert status == 200
    log("Deleted job record successfully")

    # 5. TESTING SCHEMA TYPE VALIDATION
    log("\n--- 5. Testing Schema Type Validation ---")
    status, res = request("POST", "/datasets", {
        "name": "Invalid Schema Dataset",
        "schema": [{"name": "invalid_field", "type": "unsupported_type"}]
    })
    assert status in (400, 422), f"Expected 400/422 for invalid schema, got {status}: {res}"
    log(f"Invalid schema correctly rejected with status {status}")

    # 6. TESTING DATASET DELETE
    log("\n--- 6. Testing Dataset Delete Cleanup ---")
    status, res = request("DELETE", f"/datasets/{prod_ds_id}")
    assert status == 200
    log("Product dataset deleted successfully")

    # Verify dataset is deleted
    status, res = request("GET", f"/datasets/{prod_ds_id}")
    assert status == 404

    log("\n==================================================")
    log("ALL PHASE 2 API TESTS PASSED SUCCESSFULLY!")
    log("==================================================")

if __name__ == "__main__":
    main()
