"""
Phase 4 Prompt 2 End-to-End Integration Test Script.

Tests complete pipeline:
  1. POST /api/tasks (Create Task)
  2. POST /api/tasks/{task_id}/plan (AI Planning)
  3. POST /api/tasks/{task_id}/sources/discover (Source Discovery)
  4. POST /api/tasks/{task_id}/sources/{source_id}/extract (Data Extraction)

Verifies across all 4 target research queries:
  • Jobs
  • Startups
  • Products
  • Services / Construction
"""

import sys
import time
import requests

BASE_URL = "http://127.0.0.1:8000/api"

# Force UTF-8 output encoding for Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def run_extraction_integration_tests():
    print("=" * 70)
    print("  PHASE 4 — PROMPT 2: DATA EXTRACTION ENGINE INTEGRATION TESTS")
    print("=" * 70)

    # 1. Health check
    try:
        r = requests.get(f"{BASE_URL}/health")
        assert r.status_code == 200, f"Health check failed: {r.text}"
        print("\n[✓] Backend server is live and healthy.")
    except Exception as exc:
        print(f"\n[❌] Server check failed: {exc}")
        print("Please start the FastAPI server first!")
        sys.exit(1)

    scenarios = [
        {
            "name": "Scenario 1 — Python Developer Jobs in Mumbai",
            "prompt": "Find 50 Python developer jobs in Mumbai.",
            "record_limit": 5,
        },
        {
            "name": "Scenario 2 — AI Startups in India founded after 2022",
            "prompt": "Find 30 AI startups in India founded after 2022.",
            "record_limit": 4,
        },
        {
            "name": "Scenario 3 — Laptops under ₹50,000 with at least 16GB RAM",
            "prompt": "Find laptops under ₹50,000 with at least 16GB RAM.",
            "record_limit": 3,
        },
        {
            "name": "Scenario 4 — Construction Companies in Mumbai",
            "prompt": "Find construction companies in Mumbai with their website, location and services.",
            "record_limit": 4,
        },
    ]

    for idx, s in enumerate(scenarios, 1):
        print(f"\n{'─' * 60}")
        print(f"  TEST #{idx}: {s['name']}")
        print(f"{'─' * 60}")

        # Step A: Create Task
        resp = requests.post(f"{BASE_URL}/tasks", json={"prompt": s["prompt"], "record_limit": s["record_limit"]})
        assert resp.status_code == 200, f"Create task failed: {resp.text}"
        task_data = resp.json()["data"]
        task_id = task_data["id"]
        print(f"  1. Created Task: ID={task_id}")

        # Step B: AI Plan Task
        resp = requests.post(f"{BASE_URL}/tasks/{task_id}/plan")
        assert resp.status_code == 200, f"Plan task failed: {resp.text}"
        plan_data = resp.json()["data"]
        schema = plan_data["schema"]
        field_names = [f["name"] for f in schema["fields"]]
        print(f"  2. AI Plan generated. Schema fields: {field_names}")

        # Step C: Discover Sources
        resp = requests.post(f"{BASE_URL}/tasks/{task_id}/sources/discover", json={"limit": s["record_limit"]})
        assert resp.status_code == 200, f"Discover sources failed: {resp.text}"
        disc_data = resp.json()["data"]
        sources = disc_data["sources"]
        print(f"  3. Source Discovery completed. Discovered {len(sources)} sources.")
        assert len(sources) > 0, "No sources discovered!"

        target_source = sources[0]
        source_id = target_source["id"]
        source_url = target_source["url"]
        print(f"  4. Selected Source for extraction: ID={source_id} | URL={source_url}")

        # Step D: Extract Data from Discovered Source
        resp = requests.post(f"{BASE_URL}/tasks/{task_id}/sources/{source_id}/extract")
        assert resp.status_code == 200, f"Extraction failed (Status {resp.status_code}): {resp.text}"
        ext_data = resp.json()["data"]

        print(f"  5. Extraction API Response:")
        print(f"     Status: {ext_data['status']}")
        print(f"     Total Records Extracted: {ext_data['total_records']}")

        records = ext_data["records"]
        assert len(records) > 0, "Extraction returned 0 records!"

        for r_idx, rec in enumerate(records, 1):
            print(f"     Record #{r_idx}:")
            print(f"       Data: {rec['data']}")
            print(f"       Confidence: {rec['confidence']}")
            print(f"       Source URL: {rec['source_url']}")
            # Validate provenance & fields
            assert rec["source_url"] == source_url or rec["source_url"] is not None
            assert 0.0 <= rec["confidence"] <= 1.0

        print(f"  [✓] {s['name']} PASSED successfully.")

    # 5. Testing Error Cases
    print(f"\n{'─' * 60}")
    print("  TESTING ERROR HANDLING & EDGE CASES")
    print(f"{'─' * 60}")

    # Case 1: Invalid Task ID
    resp = requests.post(f"{BASE_URL}/tasks/invalid_task_id/sources/123/extract")
    assert resp.status_code == 404, f"Expected 404 for invalid task ID, got {resp.status_code}"
    print("  [✓] Invalid task ID returned 404 as expected.")

    # Case 2: Non-existent Task ID
    resp = requests.post(f"{BASE_URL}/tasks/60f1b2c3d4e5f6a7b8c9d0e1/sources/60f1b2c3d4e5f6a7b8c9d0e2/extract")
    assert resp.status_code in (404, 409), f"Expected 404/409, got {resp.status_code}"
    print("  [✓] Non-existent task returned 404/409 as expected.")

    print("\n" + "=" * 70)
    print("  ALL PHASE 4 PROMPT 2 INTEGRATION TESTS PASSED SUCCESSFULLY! ✅")
    print("=" * 70)


if __name__ == "__main__":
    run_extraction_integration_tests()
