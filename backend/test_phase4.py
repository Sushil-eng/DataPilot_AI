"""
Phase 4 — Source Discovery Engine Tests

Tests the full source discovery pipeline:
  1. Create a task
  2. Run AI planning (Phase 3)
  3. Discover sources (Phase 4)
  4. Verify sources are generic and domain-varied

Test scenarios:
  - Python developer jobs in Mumbai
  - AI startups in India founded after 2022
  - Laptops under ₹50,000 with 16GB RAM
  - Construction companies in Mumbai
"""

import asyncio
import httpx
import json
import sys
import io

# Fix Windows console encoding for unicode characters
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://localhost:8000/api"
TIMEOUT = 60  # seconds — planning can be slow


def separator(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


async def create_task(client: httpx.AsyncClient, prompt: str, record_limit: int = 10) -> str:
    """Create a task and return its ID."""
    resp = await client.post(f"{BASE_URL}/tasks", json={
        "prompt": prompt,
        "record_limit": record_limit,
    })
    assert resp.status_code == 200, f"Task creation failed: {resp.text}"
    data = resp.json()
    task_id = data["data"]["id"]
    print(f"  ✓ Task created: {task_id}")
    print(f"    Prompt: {prompt[:80]}...")
    return task_id


async def plan_task(client: httpx.AsyncClient, task_id: str) -> dict:
    """Run AI planning and return the plan."""
    resp = await client.post(f"{BASE_URL}/tasks/{task_id}/plan", timeout=TIMEOUT)
    assert resp.status_code == 200, f"Planning failed: {resp.text}"
    data = resp.json()
    plan = data["data"]
    req = plan["requirements"]
    print(f"  ✓ Planning complete")
    print(f"    Intent: {req['intent']}")
    print(f"    Goal: {req['goal'][:80]}...")
    print(f"    Filters: {json.dumps(req.get('filters', {}))}")
    print(f"    Fields: {len(req.get('fields', []))} defined")
    return plan


async def discover_sources(client: httpx.AsyncClient, task_id: str, limit: int = 10) -> dict:
    """Run source discovery and return the response."""
    resp = await client.post(
        f"{BASE_URL}/tasks/{task_id}/sources/discover",
        json={"limit": limit},
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200, f"Discovery failed ({resp.status_code}): {resp.text}"
    data = resp.json()
    result = data["data"]
    print(f"  ✓ Sources discovered: {result['source_count']}")
    return result


def print_sources(sources: list[dict], max_show: int = 5):
    """Print source details."""
    for i, src in enumerate(sources[:max_show]):
        print(f"\n  [{i+1}] {src.get('title', 'N/A')[:60]}")
        print(f"      URL:       {src.get('url', 'N/A')[:80]}")
        print(f"      Type:      {src.get('source_type', 'N/A')}")
        print(f"      Relevance: {src.get('relevance_score', 'N/A')}")
        print(f"      Status:    {src.get('status', 'N/A')}")
    if len(sources) > max_show:
        print(f"\n  ... and {len(sources) - max_show} more sources")


async def test_scenario(
    client: httpx.AsyncClient,
    title: str,
    prompt: str,
    record_limit: int = 10,
    discover_limit: int = 10,
):
    """Run a complete test scenario: create → plan → discover."""
    separator(title)

    try:
        # Step 1: Create task
        print("  Step 1: Creating task...")
        task_id = await create_task(client, prompt, record_limit)

        # Step 2: AI Planning
        print("\n  Step 2: Running AI planning...")
        plan = await plan_task(client, task_id)

        # Step 3: Source Discovery
        print(f"\n  Step 3: Discovering sources (limit={discover_limit})...")
        result = await discover_sources(client, task_id, discover_limit)

        # Step 4: Display results
        print(f"\n  Discovered Sources:")
        print_sources(result["sources"])

        # Verify
        assert result["source_count"] > 0, "No sources discovered!"
        assert result["task_id"] == task_id, "Task ID mismatch!"
        for src in result["sources"]:
            assert "url" in src, "Source missing URL"
            assert "title" in src, "Source missing title"
            assert "source_type" in src, "Source missing type"
            assert "relevance_score" in src, "Source missing relevance"
            assert 0 <= src["relevance_score"] <= 1.0, "Score out of range"

        print(f"\n  ✅ PASS — {title}")
        return True

    except Exception as e:
        print(f"\n  ❌ FAIL — {title}: {e}")
        return False


async def test_error_cases(client: httpx.AsyncClient):
    """Test error handling."""
    separator("Error Handling Tests")
    passed = 0

    # 1. Invalid task ID
    print("  Test: Invalid task ID...")
    resp = await client.post(
        f"{BASE_URL}/tasks/invalid-id/sources/discover",
        json={"limit": 10},
    )
    assert resp.status_code in (404, 422), f"Expected 404/422, got {resp.status_code}"
    print(f"  ✓ Invalid task ID → {resp.status_code}")
    passed += 1

    # 2. Non-existent task
    print("  Test: Non-existent task...")
    resp = await client.post(
        f"{BASE_URL}/tasks/507f1f77bcf86cd799439011/sources/discover",
        json={"limit": 10},
    )
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
    print(f"  ✓ Non-existent task → 404")
    passed += 1

    # 3. Task without plan (pending)
    print("  Test: Task without plan...")
    task_resp = await client.post(f"{BASE_URL}/tasks", json={
        "prompt": "Test task no plan",
        "record_limit": 5,
    })
    task_id = task_resp.json()["data"]["id"]
    resp = await client.post(
        f"{BASE_URL}/tasks/{task_id}/sources/discover",
        json={"limit": 5},
    )
    assert resp.status_code == 409, f"Expected 409, got {resp.status_code}: {resp.text}"
    print(f"  ✓ Task without plan → 409")
    passed += 1

    print(f"\n  ✅ All {passed} error tests passed")
    return True


async def main():
    separator("Phase 4 — Source Discovery Engine Tests")
    print("  Testing the generic source discovery pipeline")
    print("  Server: " + BASE_URL)

    async with httpx.AsyncClient() as client:
        # Quick health check
        try:
            resp = await client.get(f"{BASE_URL}/health")
            assert resp.status_code == 200
            print("  ✓ Server is healthy\n")
        except Exception as e:
            print(f"  ❌ Server not reachable: {e}")
            print("  Start the server: uvicorn app.main:app --reload")
            sys.exit(1)

        results = []

        # Test 1: Jobs
        results.append(await test_scenario(
            client,
            title="Test 1: Job Search",
            prompt="Find 50 Python developer jobs in Mumbai",
            record_limit=50,
            discover_limit=10,
        ))

        # Test 2: Startups
        results.append(await test_scenario(
            client,
            title="Test 2: Startup Research",
            prompt="Find 30 AI startups in India founded after 2022",
            record_limit=30,
            discover_limit=10,
        ))

        # Test 3: Products
        results.append(await test_scenario(
            client,
            title="Test 3: Product Search",
            prompt="Find laptops under ₹50,000 with at least 16GB RAM",
            record_limit=20,
            discover_limit=10,
        ))

        # Test 4: Companies
        results.append(await test_scenario(
            client,
            title="Test 4: Company Research",
            prompt="Find construction companies in Mumbai with website, location and services",
            record_limit=20,
            discover_limit=10,
        ))

        # Error handling
        results.append(await test_error_cases(client))

        # Summary
        separator("TEST SUMMARY")
        total = len(results)
        passed = sum(1 for r in results if r)
        failed = total - passed
        print(f"  Total:  {total}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")

        if failed == 0:
            print("\n  🎉 ALL TESTS PASSED!")
        else:
            print(f"\n  ⚠️  {failed} test(s) failed")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
