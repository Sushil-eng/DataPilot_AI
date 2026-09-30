"""
Phase 4 Prompt 3 End-to-End Integration Test Script.

Tests complete pipeline:
  1. POST /api/tasks (Create Task)
  2. POST /api/tasks/{task_id}/plan (AI Planning & Dynamic Schema)
  3. POST /api/tasks/{task_id}/sources/discover (Source Discovery)
  4. POST /api/tasks/{task_id}/sources/{source_id}/extract (Data Extraction)
  5. POST /api/tasks/{task_id}/process (Data Processing Pipeline: Clean → Normalize → Validate → Deduplicate → Capped Limit)

Verifies across all 4 target research queries:
  • Jobs
  • Startups
  • Products
  • Services / Construction
"""

import sys
import requests

BASE_URL = "http://127.0.0.1:8000/api"

# Force UTF-8 output encoding for Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def run_processing_integration_tests():
    print("=" * 75)
    print("  PHASE 4 — PROMPT 3: PROCESSING PIPELINE INTEGRATION TESTS")
    print("=" * 75)

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
        print(f"\n{'─' * 65}")
        print(f"  TEST #{idx}: {s['name']}")
        print(f"{'─' * 65}")

        # Step A: Create Task
        resp = requests.post(f"{BASE_URL}/tasks", json={"prompt": s["prompt"], "record_limit": s["record_limit"]})
        assert resp.status_code == 200, f"Create task failed: {resp.text}"
        task_id = resp.json()["data"]["id"]
        print(f"  1. Task Created: ID={task_id}")

        # Step B: AI Plan Task
        resp = requests.post(f"{BASE_URL}/tasks/{task_id}/plan")
        assert resp.status_code == 200, f"Plan task failed: {resp.text}"
        schema = resp.json()["data"]["schema"]
        field_names = [f["name"] for f in schema["fields"]]
        print(f"  2. Dynamic Schema Generated: fields={field_names}")

        # Step C: Discover Sources
        resp = requests.post(f"{BASE_URL}/tasks/{task_id}/sources/discover", json={"limit": s["record_limit"]})
        assert resp.status_code == 200, f"Discover sources failed: {resp.text}"
        sources = resp.json()["data"]["sources"]
        print(f"  3. Sources Discovered: count={len(sources)}")
        assert len(sources) > 0

        # Step D: Extract Data
        source_id = sources[0]["id"]
        resp = requests.post(f"{BASE_URL}/tasks/{task_id}/sources/{source_id}/extract")
        assert resp.status_code == 200, f"Extraction failed: {resp.text}"
        raw_recs = resp.json()["data"]["records"]
        print(f"  4. Raw Extraction Complete: extracted {len(raw_recs)} raw records.")

        # Step E: Process Pipeline (Clean → Normalize → Validate → Deduplicate → Capped Limit)
        resp = requests.post(f"{BASE_URL}/tasks/{task_id}/process")
        assert resp.status_code == 200, f"Processing pipeline failed: {resp.text}"
        proc_data = resp.json()["data"]

        print(f"  5. Processing Pipeline Execution Result:")
        print(f"     • Input Count:        {proc_data['input_count']}")
        print(f"     • Cleaned Count:      {proc_data['cleaned_count']}")
        print(f"     • Valid Count:        {proc_data['valid_count']}")
        print(f"     • Invalid Count:      {proc_data['invalid_count']}")
        print(f"     • Duplicates Removed: {proc_data['duplicates_removed']}")
        print(f"     • Final Count:        {proc_data['final_count']}")

        final_records = proc_data["records"]
        assert len(final_records) <= s["record_limit"], f"Final count {len(final_records)} exceeds limit {s['record_limit']}"

        for r_idx, rec in enumerate(final_records, 1):
            print(f"     Final Record #{r_idx}:")
            print(f"       Data: {rec['data']}")
            print(f"       Validation Status: {rec.get('validation_status')}")
            print(f"       Confidence: {rec.get('confidence')}")

            # Check that validation status is valid
            assert rec.get("validation_status") == "valid"

        print(f"  [✓] {s['name']} PASSED successfully.")

    # 6. Testing Error Cases & Direct Body Injection
    print(f"\n{'─' * 65}")
    print("  TESTING DIRECT RECORD INJECTION & ERROR HANDLING")
    print(f"{'─' * 65}")

    # Case A: Direct record body processing with malformed & duplicate data
    test_body = {
        "records": [
            {"data": {"company_name": "  Aura   AI  ", "location": "Mumbai", "website": "HTTPS://Aura.AI/", "services": ["Civil"], "source_url": "https://aura.ai"}, "source_url": "https://aura.ai"},
            {"data": {"company_name": "Aura AI", "location": "Mumbai", "website": "https://aura.ai", "services": ["Civil"], "source_url": "https://aura.ai"}, "source_url": "https://aura.ai"},  # Exact Dup
            {"data": {"company_name": None, "location": "Mumbai", "website": "https://invalid.com", "services": ["Civil"], "source_url": "https://invalid.com"}, "source_url": "https://invalid.com"},  # Invalid missing name
        ]
    }
    resp = requests.post(f"{BASE_URL}/tasks/{task_id}/process", json=test_body)
    assert resp.status_code == 200
    res_data = resp.json()["data"]
    print(f"  Direct Injection Result: Input={res_data['input_count']}, Valid={res_data['valid_count']}, Invalid={res_data['invalid_count']}, DupRemoved={res_data['duplicates_removed']}, Final={res_data['final_count']}")
    assert res_data["input_count"] == 3
    assert res_data["valid_count"] == 2
    assert res_data["invalid_count"] == 1
    assert res_data["duplicates_removed"] == 1
    assert res_data["final_count"] == 1
    print("  [✓] Direct record injection with clean, normalize, validate, dedup PASSED successfully.")

    # Case B: Invalid Task ID
    resp = requests.post(f"{BASE_URL}/tasks/invalid_task_id/process")
    assert resp.status_code == 404
    print("  [✓] Invalid task ID returned 404 as expected.")

    print("\n" + "=" * 75)
    print("  ALL PHASE 4 PROMPT 3 INTEGRATION TESTS PASSED SUCCESSFULLY! ✅")
    print("=" * 75)


if __name__ == "__main__":
    run_processing_integration_tests()
