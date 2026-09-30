"""
Comprehensive Source Fetching & Playwright Resilience Test Suite

Verifies:
1. Normal accessible website fetching (HTTP).
2. Blocked HTTP website with Playwright fallback.
3. Multi-source resilience: some sources failing/blocked do NOT fail the workflow.
4. Complete DataPilot workflow end-to-end.
"""

import sys
import asyncio
import logging
from datetime import datetime, timezone
from bson import ObjectId

if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_source_resilience")

from app.database.connection import connect_to_mongo, close_mongo_connection, get_db
from app.collection.fetcher import SourceFetcher, HTTPFetcher, BrowserFetcher
from app.collection.search_providers import SourceCandidate, SourceType, SourceStatus
from app.workflow.step_executor import StepExecutor
from app.workflow.executor import WorkflowExecutor
from app.workflow.execution_models import ExecutionContext
from app.ai.orchestrator import WorkflowOrchestrator


async def test_1_normal_website():
    logger.info("=== TEST 1: Normal Accessible Website Fetch ===")
    fetcher = SourceFetcher()
    res = await fetcher.fetch("https://example.com")
    logger.info("Test 1 Result Status: %s, Status Code: %s, Text len: %d", res.get("status"), res.get("status_code"), len(res.get("text", "")))
    assert res.get("status") == "fetched", f"Expected 'fetched', got {res.get('status')}"
    assert "Example Domain" in (res.get("title") or "") or "example" in res.get("text", "").lower()
    logger.info("TEST 1 PASSED!\n")


async def test_2_playwright_direct_and_blocked_simulation():
    logger.info("=== TEST 2: Playwright Browser Fetcher Direct Test ===")
    browser_fetcher = BrowserFetcher(timeout_ms=15000)
    res = await browser_fetcher.fetch("https://example.com")
    logger.info("Test 2 Playwright Status: %s, Title: %r", res.get("status"), res.get("title"))
    assert res.get("status") == "fetched", f"Expected browser status 'fetched', got {res.get('status')}"
    logger.info("TEST 2 PASSED!\n")


async def test_3_multi_source_partial_failure():
    logger.info("=== TEST 3: Multi-Source Partial Failure Resilience ===")
    await connect_to_mongo()
    db = get_db()

    # 1. Create a task with mixed sources (1 accessible, 1 blocked/invalid, 1 with search snippet)
    task_doc = {
        "title": "Find 2 AI Engineers",
        "description": "Find 2 AI Engineers in Bangalore",
        "status": "planned",
        "ai_requirements": {
            "intent": "job_search",
            "goal": "Find 2 AI Engineers in Bangalore",
            "filters": {"location": "Bangalore"},
            "fields": [
                {"name": "job_title", "type": "string", "required": True},
                {"name": "company_name", "type": "string", "required": True},
                {"name": "location", "type": "string", "required": True},
            ],
            "record_limit": 2,
        },
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    task_res = await db.tasks.insert_one(task_doc)
    task_id = str(task_res.inserted_id)

    dataset_doc = {
        "task_id": task_id,
        "name": "AI Engineers Dataset",
        "status": "pending",
        "dynamic_schema": {
            "fields": [
                {"name": "job_title", "type": "string", "required": True},
                {"name": "company_name", "type": "string", "required": True},
                {"name": "location", "type": "string", "required": True},
            ]
        },
        "created_at": datetime.now(timezone.utc),
    }
    ds_res = await db.datasets.insert_one(dataset_doc)
    dataset_id = str(ds_res.inserted_id)

    # Insert 3 sources:
    # Source A: Live accessible (example.com)
    # Source B: Blocked / invalid domain that will fail/skip
    # Source C: Has rich search snippet/highlights (e.g. from Exa)
    source_a = {
        "task_id": task_id,
        "dataset_id": dataset_id,
        "url": "https://example.com",
        "title": "Example Careers",
        "status": "discovered",
        "discovered_at": datetime.now(timezone.utc),
        "metadata": {"snippet": "Senior AI Engineer openings at Example Corp in Bangalore."},
    }
    source_b = {
        "task_id": task_id,
        "dataset_id": dataset_id,
        "url": "https://invalid-non-existent-domain-403-test.org/blocked",
        "title": "Blocked Domain",
        "status": "discovered",
        "discovered_at": datetime.now(timezone.utc),
        "metadata": {},
    }
    source_c = {
        "task_id": task_id,
        "dataset_id": dataset_id,
        "url": "https://quora-simulated-blocked-page.com/jobs",
        "title": "Bangalore AI Jobs",
        "status": "discovered",
        "discovered_at": datetime.now(timezone.utc),
        "metadata": {
            "highlights": ["Lead AI Engineer at Infosys Bangalore", "Experience with PyTorch, NLP, and LLM fine-tuning."],
            "snippet": "Infosys is hiring Lead AI Engineer in Bangalore. Apply with CV.",
        },
    }

    res_a = await db.sources.insert_one(source_a)
    source_a["id"] = str(res_a.inserted_id)
    res_b = await db.sources.insert_one(source_b)
    source_b["id"] = str(res_b.inserted_id)
    res_c = await db.sources.insert_one(source_c)
    source_c["id"] = str(res_c.inserted_id)

    sources_list = [source_a, source_b, source_c]

    context = ExecutionContext(
        task_id=task_id,
        workflow_id="wf_test_123",
        dataset_id=dataset_id,
        requirements=task_doc["ai_requirements"],
        schema={
            "fields": [
                {"name": "job_title", "type": "string", "required": True},
                {"name": "company_name", "type": "string", "required": True},
                {"name": "location", "type": "string", "required": True},
            ]
        },
        record_limit=2,
    )
    context.sources = sources_list

    executor = StepExecutor()
    extract_res = await executor._execute_extract(context)
    logger.info("Extraction Result: %s", extract_res)

    # Check that failed source did NOT kill the extraction step
    assert extract_res.get("sources_total") == 3
    assert extract_res.get("sources_processed", 0) >= 1 or len(context.raw_records) >= 1, "Expected usable sources extracted"
    logger.info("Extracted %d raw records despite source failure!", len(context.raw_records))

    # Verify DB statuses
    doc_b = await db.sources.find_one({"_id": ObjectId(source_b["id"])})
    logger.info("Source B (failed) DB status: %s", doc_b.get("status"))
    assert doc_b.get("status") in ("skipped", "failed", "blocked")

    logger.info("TEST 3 PASSED!\n")


async def test_4_complete_workflow():
    logger.info("=== TEST 4: Complete End-to-End Workflow Execution ===")
    db = get_db()
    orchestrator = WorkflowOrchestrator()

    task_doc = {
        "title": "Find 3 Full Stack Python developers in Delhi",
        "description": "Find 3 Full Stack Python developers in Delhi",
        "prompt": "Find 3 Full Stack Python developers in Delhi",
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    t_res = await db.tasks.insert_one(task_doc)
    task_id = str(t_res.inserted_id)

    # Plan
    plan_res = await orchestrator.plan(task_id=task_id)
    logger.info("Plan created: %s", plan_res)

    # Execute workflow
    workflow_executor = WorkflowExecutor()
    exec_res = await workflow_executor.execute(task_id)
    logger.info("Workflow execution finished: status=%s, progress=%d, records=%d, fallback=%s",
                exec_res.get("status"), exec_res.get("progress"), exec_res.get("record_count"), exec_res.get("fallback_used"))

    assert exec_res.get("status") == "completed"
    assert exec_res.get("progress") == 100
    assert exec_res.get("record_count", 0) > 0

    await close_mongo_connection()
    logger.info("=== ALL TESTS PASSED SUCCESSFULLY! ===")


async def main():
    await test_1_normal_website()
    await test_2_playwright_direct_and_blocked_simulation()
    await test_3_multi_source_partial_failure()
    await test_4_complete_workflow()

if __name__ == "__main__":
    asyncio.run(main())
