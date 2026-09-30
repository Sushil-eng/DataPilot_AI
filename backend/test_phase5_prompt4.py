"""
Phase 5 Prompt 4 — Final Testing & Integration Verification Script

Tests:
1. Auth Endpoints (Register, Login, Me, Bad Auth)
2. Task Endpoints (Create, List, Get, Update, Delete, Plan)
3. Workflow Endpoints (Get, Steps, Progress)
4. Full End-to-End Pipeline Execution for 4 Prompts:
   - "Find 30 AI startups in India founded after 2022"
   - "Find Python developer jobs in Mumbai"
   - "Find laptops under ₹50,000 with at least 16GB RAM"
   - "Find construction companies in Mumbai with website, location and services"
5. Datasets Endpoints (List, Get, Records, Search/Filter, Export)
6. Analytics Endpoints (Overview, Activity, Dataset Analytics)
7. Error Handling & Security checks (400, 401, 404, 422, non-existent objects, ownership check)
"""

import asyncio
import httpx
import json
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://localhost:8000/api"
TIMEOUT = 120.0

def print_hdr(title: str):
    print(f"\n{'='*75}")
    print(f"  {title}")
    print(f"{'='*75}")

async def run_tests():
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        timestamp = int(time.time())
        test_email = f"testuser_{timestamp}@example.com"
        test_pass = "TestPassword123!"
        
        # ----------------------------------------------------
        # 1. AUTHENTICATION TESTS
        # ----------------------------------------------------
        print_hdr("1. AUTHENTICATION TESTS")
        
        # Register
        print("[1.1] Registering user...")
        resp = await client.post(f"{BASE_URL}/auth/register", json={
            "email": test_email,
            "password": test_pass,
            "full_name": "Test User"
        })
        assert resp.status_code in [200, 201], f"Register failed ({resp.status_code}): {resp.text}"
        reg_data = resp.json()["data"]
        token = reg_data["access_token"]
        user_id = reg_data["user"]["id"]
        print(f"  ✓ User registered. ID: {user_id}, Token received.")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Current User (Me)
        print("[1.2] Checking GET /auth/me...")
        resp = await client.get(f"{BASE_URL}/auth/me", headers=headers)
        assert resp.status_code == 200, f"Me failed: {resp.text}"
        me_data = resp.json()["data"]
        assert me_data["email"] == test_email
        print(f"  ✓ GET /auth/me returned correct user: {me_data['email']}")
        
        # Login
        print("[1.3] Testing POST /auth/login...")
        resp = await client.post(f"{BASE_URL}/auth/login", json={
            "email": test_email,
            "password": test_pass
        })
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        login_token = resp.json()["data"]["access_token"]
        assert login_token is not None
        print("  ✓ Login successful.")
        
        # Invalid Login
        print("[1.4] Testing invalid login...")
        resp = await client.post(f"{BASE_URL}/auth/login", json={
            "email": test_email,
            "password": "wrongpassword"
        })
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print(f"  ✓ Invalid login correctly returned 401: {resp.json()['error']['message']}")
        
        # Unauthorized Endpoint Call
        print("[1.5] Testing unauthorized access...")
        resp = await client.get(f"{BASE_URL}/auth/me")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print(f"  ✓ Unauthenticated request rejected: 401")

        # Create second user for authorization isolation testing
        user2_email = f"user2_{timestamp}@example.com"
        resp2 = await client.post(f"{BASE_URL}/auth/register", json={
            "email": user2_email,
            "password": test_pass,
            "full_name": "Second User"
        })
        token2 = resp2.json()["data"]["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        # ----------------------------------------------------
        # 2. TASK CRUD & WORKFLOW TESTS
        # ----------------------------------------------------
        print_hdr("2. TASK CRUD & MANAGEMENT TESTS")
        
        # Create Task
        print("[2.1] Creating a test task...")
        resp = await client.post(f"{BASE_URL}/tasks", json={
            "prompt": "Find Python developer jobs in Mumbai",
            "record_limit": 5
        }, headers=headers)
        assert resp.status_code == 200, f"Task create failed: {resp.text}"
        task1 = resp.json()["data"]
        task1_id = task1["id"]
        print(f"  ✓ Created Task ID: {task1_id}")
        
        # Get Task
        print("[2.2] Getting task by ID...")
        resp = await client.get(f"{BASE_URL}/tasks/{task1_id}", headers=headers)
        assert resp.status_code == 200
        print(f"  ✓ Fetched task status: {resp.json()['data']['status']}")
        
        # List Tasks
        print("[2.3] Listing tasks for user...")
        resp = await client.get(f"{BASE_URL}/tasks", headers=headers)
        assert resp.status_code == 200
        tasks_res = resp.json()["data"]
        tasks_list = tasks_res.get("items", []) if isinstance(tasks_res, dict) else tasks_res
        assert any(t.get("id") == task1_id or t.get("_id") == task1_id for t in tasks_list)
        print(f"  ✓ List returned {len(tasks_list)} tasks.")

        # Update Task
        print("[2.4] Updating task...")
        resp = await client.patch(f"{BASE_URL}/tasks/{task1_id}", json={
            "prompt": "Find top Python developer jobs in Mumbai"
        }, headers=headers)
        assert resp.status_code == 200, f"Task update failed ({resp.status_code}): {resp.text}"
        assert resp.json()["data"]["prompt"] == "Find top Python developer jobs in Mumbai"
        print("  ✓ Task prompt updated successfully.")
        
        # User Isolation Check
        print("[2.5] Testing user isolation for tasks...")
        resp = await client.get(f"{BASE_URL}/tasks/{task1_id}", headers=headers2)
        assert resp.status_code == 404 or resp.status_code == 403, f"Expected 404/403, got {resp.status_code}"
        print(f"  ✓ Access by user2 blocked: {resp.status_code}")

        # ----------------------------------------------------
        # 3. END-TO-END PIPELINE EXECUTIONS (4 PROMPTS)
        # ----------------------------------------------------
        print_hdr("3. END-TO-END PIPELINE EXECUTIONS FOR 4 SCENARIOS")

        prompts = [
            ("AI Startups", "Find 30 AI startups in India founded after 2022.", 5),
            ("Python Developer Jobs", "Find Python developer jobs in Mumbai.", 5),
            ("Laptops under 50k", "Find laptops under ₹50,000 with at least 16GB RAM.", 5),
            ("Construction Companies", "Find construction companies in Mumbai with website, location and services.", 5)
        ]

        completed_datasets = []

        for name, prompt_str, rec_limit in prompts:
            print(f"\n--- Running scenario: '{name}' ---")
            # 1. Create task
            resp = await client.post(f"{BASE_URL}/tasks", json={
                "prompt": prompt_str,
                "record_limit": rec_limit
            }, headers=headers)
            assert resp.status_code == 200
            t_id = resp.json()["data"]["id"]
            print(f"  [Task] Created: {t_id}")

            # 2. Plan task
            resp = await client.post(f"{BASE_URL}/tasks/{t_id}/plan", headers=headers)
            assert resp.status_code == 200
            plan_data = resp.json()["data"]
            print(f"  [AI Plan] Schema fields: {len(plan_data['schema']['fields']) if plan_data.get('schema') else 'N/A'}")

            # 3. Execute workflow
            resp = await client.post(f"{BASE_URL}/tasks/{t_id}/execute", headers=headers)
            assert resp.status_code == 200
            print(f"  [Execute] Workflow triggered.")

            # 4. Poll task status & progress
            attempts = 0
            max_attempts = 40
            task_status = "pending"
            dataset_id = None

            while attempts < max_attempts and task_status not in ["completed", "failed"]:
                await asyncio.sleep(2)
                attempts += 1
                r_status = await client.get(f"{BASE_URL}/tasks/{t_id}", headers=headers)
                t_data = r_status.json()["data"]
                task_status = t_data.get("status")
                dataset_id = t_data.get("dataset_id")
                
                # Check workflow progress endpoint
                r_wf = await client.get(f"{BASE_URL}/workflows/{t_id}", headers=headers)
                if r_wf.status_code == 200:
                    wf_data = r_wf.json()["data"]
                    steps_comp = sum(1 for s in wf_data.get("steps", []) if s.get("status") == "completed")
                    tot_steps = len(wf_data.get("steps", []))
                    if attempts % 3 == 0:
                        print(f"    Waiting... status={task_status}, steps={steps_comp}/{tot_steps}")

            assert task_status == "completed", f"Task {t_id} failed or timed out: status={task_status}"
            assert dataset_id is not None, f"No dataset_id produced for completed task {t_id}"
            print(f"  ✓ Completed successfully! Dataset ID: {dataset_id}")
            completed_datasets.append((t_id, dataset_id))

        # ----------------------------------------------------
        # 4. DATASETS & RECORDS & EXPORT TESTS
        # ----------------------------------------------------
        print_hdr("4. DATASETS, RECORDS, & EXPORT TESTS")

        assert len(completed_datasets) > 0
        sample_task_id, sample_dataset_id = completed_datasets[0]

        # List Datasets
        print("[4.1] Listing datasets...")
        resp = await client.get(f"{BASE_URL}/datasets", headers=headers)
        assert resp.status_code == 200
        datasets = resp.json()["data"]
        print(f"  ✓ Total datasets returned: {len(datasets)}")

        # Get Dataset Details
        print(f"[4.2] Fetching dataset {sample_dataset_id}...")
        resp = await client.get(f"{BASE_URL}/datasets/{sample_dataset_id}", headers=headers)
        assert resp.status_code == 200
        ds_info = resp.json()["data"]
        print(f"  ✓ Dataset name: {ds_info.get('name')}, record_count: {ds_info.get('record_count')}")

        # Get Records with Pagination & Search
        print(f"[4.3] Fetching dataset records with pagination...")
        resp = await client.get(f"{BASE_URL}/datasets/{sample_dataset_id}/records?page=1&limit=2", headers=headers)
        assert resp.status_code == 200
        recs_data = resp.json()["data"]
        recs = recs_data.get("items", recs_data.get("records", []))
        print(f"  ✓ Pagination returned {len(recs)} records (total: {recs_data.get('total')})")

        # Search Records
        print(f"[4.4] Searching records...")
        resp = await client.get(f"{BASE_URL}/datasets/{sample_dataset_id}/records?search=a", headers=headers)
        assert resp.status_code == 200
        print(f"  ✓ Search query executed successfully.")

        # Export CSV
        print(f"[4.5] Exporting dataset as CSV...")
        resp = await client.get(f"{BASE_URL}/datasets/{sample_dataset_id}/export?format=csv", headers=headers)
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")
        print(f"  ✓ CSV Export received ({len(resp.content)} bytes)")

        # Export JSON
        print(f"[4.6] Exporting dataset as JSON...")
        resp = await client.get(f"{BASE_URL}/datasets/{sample_dataset_id}/export?format=json", headers=headers)
        assert resp.status_code == 200
        assert "application/json" in resp.headers.get("content-type", "")
        print(f"  ✓ JSON Export received ({len(resp.content)} bytes)")

        # Dataset User Isolation Check
        print(f"[4.7] Testing dataset user isolation...")
        resp = await client.get(f"{BASE_URL}/datasets/{sample_dataset_id}", headers=headers2)
        assert resp.status_code in [403, 404], f"Expected 403/404 for user isolation, got {resp.status_code}"
        print(f"  ✓ User 2 blocked from accessing user 1's dataset: {resp.status_code}")

        # ----------------------------------------------------
        # 5. ANALYTICS TESTS
        # ----------------------------------------------------
        print_hdr("5. ANALYTICS ENDPOINTS TESTS")

        # Overview
        print("[5.1] Testing GET /analytics/overview...")
        resp = await client.get(f"{BASE_URL}/analytics/overview", headers=headers)
        assert resp.status_code == 200
        ov = resp.json()["data"]
        print(f"  ✓ Analytics overview: total_tasks={ov.get('total_tasks')}, total_records={ov.get('total_records')}")

        # Activity
        print("[5.2] Testing GET /analytics/activity...")
        resp = await client.get(f"{BASE_URL}/analytics/activity", headers=headers)
        assert resp.status_code == 200
        act = resp.json()["data"]
        print(f"  ✓ Analytics activity returned {len(act)} activity entries.")

        # Dataset Analytics
        print(f"[5.3] Testing GET /analytics/datasets/{sample_dataset_id}...")
        resp = await client.get(f"{BASE_URL}/analytics/datasets/{sample_dataset_id}", headers=headers)
        assert resp.status_code == 200
        ds_an = resp.json()["data"]
        print(f"  ✓ Dataset analytics: record_count={ds_an.get('record_count')}, completeness={ds_an.get('completeness_rate')}%")

        # ----------------------------------------------------
        # 6. ERROR HANDLING & SECURITY AUDIT TESTS
        # ----------------------------------------------------
        print_hdr("6. ERROR HANDLING & SECURITY CORNER CASES")

        # Non-existent Task ID
        print("[6.1] Fetching non-existent task ID...")
        resp = await client.get(f"{BASE_URL}/tasks/650000000000000000000000", headers=headers)
        assert resp.status_code == 404
        err = resp.json()
        assert err["success"] is False
        assert "message" in err["error"]
        print(f"  ✓ Correct JSON 404 response: {err['error']['message']}")

        # Invalid Task ID format
        print("[6.2] Fetching invalid task ID string...")
        resp = await client.get(f"{BASE_URL}/tasks/invalid-object-id-123", headers=headers)
        assert resp.status_code in [400, 404, 422], f"Expected 400/404/422, got {resp.status_code}"
        err = resp.json()
        assert err["success"] is False
        print(f"  ✓ Correct JSON invalid ID response: {err['error']['message']}")

        # Non-existent Dataset ID
        print("[6.3] Fetching non-existent dataset ID...")
        resp = await client.get(f"{BASE_URL}/datasets/650000000000000000000000", headers=headers)
        assert resp.status_code == 404
        print(f"  ✓ Correct JSON 404 response for missing dataset.")

        # Delete Task
        print("[6.4] Testing task deletion...")
        resp = await client.delete(f"{BASE_URL}/tasks/{task1_id}", headers=headers)
        assert resp.status_code == 200
        print(f"  ✓ Task deleted.")

        resp = await client.get(f"{BASE_URL}/tasks/{task1_id}", headers=headers)
        assert resp.status_code == 404
        print(f"  ✓ Task is verified deleted (404).")

        print_hdr("ALL INTEGRATION TESTS COMPLETED SUCCESSFULLY! 🎉")

if __name__ == "__main__":
    asyncio.run(run_tests())
