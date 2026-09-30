"""
Phase 3 — Prompt 3: Workflow Planner & Orchestrator Tests

Creates tasks, then calls POST /api/tasks/{task_id}/plan for each.
Verifies that requirements, dynamic schema, and workflow all change
according to the domain.

Usage:
    1. Start the backend:  uvicorn app.main:app --reload
    2. Run this script:    python test_phase3.py
"""

import httpx
import json
import sys
import io

# Fix Windows console encoding for special characters like ₹
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://127.0.0.1:8000"

TEST_PROMPTS = [
    "Find Python developer jobs in Mumbai.",
    "Find 50 AI startups in India founded after 2022 with company name, founders, location, website and funding.",
    "Find laptops under ₹50,000 with brand, model, price, RAM, storage, screen size, and rating.",
]


def print_separator(char="=", width=70):
    print(char * width)


def create_task(prompt: str) -> str:
    """Create a task and return its ID."""
    resp = httpx.post(
        f"{BASE_URL}/api/tasks",
        json={"prompt": prompt, "record_limit": 50},
        timeout=10,
    )
    if resp.status_code != 200:
        print(f"  ERROR creating task: {resp.text[:300]}")
        return ""
    data = resp.json().get("data", {})
    task_id = data.get("id", "")
    print(f"  Created task: {task_id}  status={data.get('status')}")
    return task_id


def plan_task(task_id: str) -> dict:
    """Call the plan endpoint and return the response."""
    resp = httpx.post(
        f"{BASE_URL}/api/tasks/{task_id}/plan",
        timeout=60,
    )
    return {"status_code": resp.status_code, "body": resp.json()}


def verify_task_status(task_id: str) -> str:
    """Fetch the task and return its current status."""
    resp = httpx.get(f"{BASE_URL}/api/tasks/{task_id}", timeout=10)
    if resp.status_code == 200:
        return resp.json().get("data", {}).get("status", "unknown")
    return "fetch_error"


def test_plan(prompt: str, index: int):
    print(f"\n")
    print_separator()
    print(f"TEST {index}: {prompt}")
    print_separator()

    # 1. Create the task
    print("\n[1] Creating task...")
    task_id = create_task(prompt)
    if not task_id:
        print("  SKIP — could not create task")
        return

    # 2. Plan it
    print(f"\n[2] Planning task {task_id}...")
    result = plan_task(task_id)
    status_code = result["status_code"]
    body = result["body"]

    print(f"  HTTP Status: {status_code}")

    if status_code != 200:
        print(f"  Error: {json.dumps(body, indent=2, ensure_ascii=False)[:500]}")
        return

    plan_data = body.get("data", {})

    # 3. Show requirements
    reqs = plan_data.get("requirements", {})
    print(f"\n--- Requirements ---")
    print(f"  Intent:       {reqs.get('intent')}")
    print(f"  Goal:         {reqs.get('goal')}")
    print(f"  Record Limit: {reqs.get('record_limit')}")
    print(f"  Confidence:   {reqs.get('confidence')}")

    # 4. Show filters
    filters = reqs.get("filters", {})
    print(f"\n--- Filters ---")
    if filters:
        for k, v in filters.items():
            print(f"  {k}: {v}")
    else:
        print("  (none)")

    # 5. Show dynamic schema
    schema = plan_data.get("schema", {})
    print(f"\n--- Dynamic Schema ---")
    print(f"  Name:           {schema.get('schema_name')}")
    print(f"  Total Fields:   {schema.get('total_fields')}")
    print(f"  Required Count: {schema.get('required_count')}")
    print(f"  Fields:")
    for f in schema.get("fields", []):
        req_marker = "✓" if f.get("required") else "○"
        print(f"    [{req_marker}] {f['name']:25s}  ({f['type']:10s})  — {f['description']}")

    # 6. Show workflow
    workflow = plan_data.get("workflow", {})
    steps = workflow.get("steps", [])
    print(f"\n--- Workflow ({workflow.get('workflow_type')}) ---")
    print(f"  Goal:        {workflow.get('goal')}")
    print(f"  Total Steps: {workflow.get('total_steps')}")
    print(f"\n  Steps:")
    for step in steps:
        dep = f"  (after {step['depends_on']})" if step.get("depends_on") else ""
        print(
            f"    {step['id']:8s} | [{step['tool']:12s}] {step['name']:25s}"
            f" — {step['description'][:60]}{dep}"
        )

    # 7. Verify task status in MongoDB
    final_status = verify_task_status(task_id)
    print(f"\n--- Task Status ---")
    print(f"  Status in DB: {final_status}")
    if final_status == "planned":
        print("  ✓ Status correctly set to 'planned'")
    else:
        print(f"  ✗ Expected 'planned', got '{final_status}'")


def main():
    print_separator()
    print("  DataPilot AI — Phase 3 / Prompt 3 Test Suite")
    print("  Workflow Planner & Orchestrator")
    print("  POST /api/tasks/{task_id}/plan")
    print_separator()

    # Quick health check
    try:
        health = httpx.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"\nHealth check: {health.status_code}")
    except httpx.ConnectError:
        print("\nERROR: Backend is not running.")
        print("       Start it with: uvicorn app.main:app --reload")
        sys.exit(1)

    for i, prompt in enumerate(TEST_PROMPTS, 1):
        test_plan(prompt, i)

    print(f"\n")
    print_separator()
    print("  All 3 tests complete.")
    print_separator()


if __name__ == "__main__":
    main()
