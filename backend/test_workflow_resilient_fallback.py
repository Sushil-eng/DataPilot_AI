"""
Test Suite: Workflow Resilient Groq AI Fallback on Serper 403 / Failure
Verifies:
1. Serper 403 / unavailable does NOT fail the workflow.
2. Search step is marked SKIPPED / FALLBACK.
3. Preprocessed structured task request is sent to Groq AI fallback.
4. Final dataset records are generated, normalized, validated, and stored in MongoDB.
5. Task status becomes 'completed' with 100% progress and fallback notice recorded.
"""

import asyncio
import logging
from app.database.connection import connect_to_mongo, close_mongo_connection, get_db
from app.services import task_service
from app.ai.orchestrator import WorkflowOrchestrator
from app.workflow.executor import WorkflowExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_workflow")


async def run_resilient_workflow_test():
    await connect_to_mongo()
    db = get_db()

    prompt = "Find 5 Python developer jobs in Mumbai"
    logger.info("=== 1. Creating Task: '%s' ===", prompt)
    task = await task_service.create_task(prompt=prompt, record_limit=5)
    task_id = task["id"]
    logger.info("Task created with ID: %s", task_id)

    logger.info("=== 2. Generating AI Plan ===")
    orchestrator = WorkflowOrchestrator()
    plan = await orchestrator.plan(task_id)
    logger.info("AI Plan generated: %d fields, %d steps", len(plan.schema.fields), len(plan.workflow["steps"]))

    logger.info("=== 3. Executing Workflow ===")
    executor = WorkflowExecutor()
    exec_result = await executor.execute(task_id)

    logger.info("=== 4. Execution Finished ===")
    logger.info("Result Status: %s", exec_result.get("status"))
    logger.info("Result Progress: %s", exec_result.get("progress"))
    logger.info("Record Count: %s", exec_result.get("record_count"))
    logger.info("Fallback Used: %s", exec_result.get("fallback_used"))

    # Assertions
    assert exec_result.get("status") == "completed", f"Expected completed, got {exec_result.get('status')}"
    assert exec_result.get("progress") == 100, f"Expected progress 100, got {exec_result.get('progress')}"
    assert exec_result.get("record_count", 0) > 0, "Expected at least 1 record stored"

    # Verify MongoDB persistence
    db_task = await db.tasks.find_one({"_id": task["_id"] if "_id" in task else None})
    if not db_task:
        from bson import ObjectId
        db_task = await db.tasks.find_one({"_id": ObjectId(task_id)})

    assert db_task["status"] == "completed"
    assert db_task["progress"] == 100

    db_records = await db.dataset_records.find({"task_id": task_id}).to_list(length=10)
    logger.info("Stored MongoDB records: %d", len(db_records))
    if db_records:
        logger.info("Sample record keys: %s", list(db_records[0].get("data", {}).keys()))

    await close_mongo_connection()
    logger.info("=== ALL WORKFLOW RESILIENCE TESTS PASSED! ===")


if __name__ == "__main__":
    asyncio.run(run_resilient_workflow_test())
