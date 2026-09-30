"""
Comprehensive Integration Test Suite for Phase 4 Prompt 4 — Workflow Execution Engine.
Tests full end-to-end planning + workflow execution across all 4 research scenarios and failure edge cases.
"""

import sys
import os
import asyncio
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import connect_to_mongo, close_mongo_connection, get_db
from app.services import task_service
from app.ai.orchestrator import WorkflowOrchestrator
from app.workflow.executor import WorkflowExecutor, WorkflowExecutorError
from app.workflow.step_executor import StepExecutor, StepExecutionError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_phase4_prompt4")


TEST_PROMPTS = [
    ("Find 50 Python developer jobs in Mumbai.", 50),
    ("Find 30 AI startups in India founded after 2022.", 30),
    ("Find laptops under Rs.50,000 with at least 16GB RAM.", 20),
    ("Find construction companies in Mumbai with website, location and services.", 15),
]


async def run_scenario_tests():
    print("\n==================================================")
    print("RUNNING PHASE 4 PROMPT 4 INTEGRATION TESTS")
    print("==================================================")

    await connect_to_mongo()
    db = get_db()
    executor = WorkflowExecutor()

    for idx, (prompt, limit) in enumerate(TEST_PROMPTS, 1):
        print(f"\n--- Scenario {idx}: {prompt} (limit={limit}) ---")

        # 1. Create task
        task_res = await task_service.create_task(prompt=prompt, record_limit=limit)
        task_id = task_res["id"]
        print(f"[OK] Task created: {task_id}")

        # 2. Plan task (Phase 3 AI planner)
        orchestrator = WorkflowOrchestrator()
        plan_res = await orchestrator.plan(task_id)
        assert plan_res is not None
        print(f"[OK] AI Planning completed for task {task_id}")

        # Verify task state after planning
        task_doc = await db.tasks.find_one({"_id": task_res["_id"] if "_id" in task_res else None})
        if not task_doc:
            from bson import ObjectId
            task_doc = await db.tasks.find_one({"_id": ObjectId(task_id)})

        assert task_doc["status"] == "planned"
        print(f"[OK] Task status: {task_doc['status']}")

        # Verify workflow document exists
        wf_doc = await db.workflows.find_one({"task_id": task_id})
        assert wf_doc is not None
        assert len(wf_doc["steps"]) > 0
        print(f"[OK] Workflow contains {len(wf_doc['steps'])} steps")

        # 3. Execute Workflow
        exec_res = await executor.execute(task_id)
        print(f"[OK] Execution finished with status: {exec_res.get('status')}")
        assert exec_res["status"] == "completed"

        # 4. Verify MongoDB Task document
        task_after = await db.tasks.find_one({"_id": task_doc["_id"]})
        assert task_after["status"] == "completed"
        assert task_after["progress"] == 100
        assert task_after["record_count"] <= limit
        print(f"[OK] Final task status: {task_after['status']}, progress: {task_after['progress']}%, record_count: {task_after['record_count']}")

        # 5. Verify MongoDB Workflow document
        wf_after = await db.workflows.find_one({"task_id": task_id})
        assert wf_after["status"] == "completed"
        assert wf_after["progress"] == 100
        assert "execution_stats" in wf_after
        stats = wf_after["execution_stats"]
        print(f"[OK] Workflow execution stats: {stats}")

        # 6. Verify MongoDB Dataset document and Records
        ds_after = await db.datasets.find_one({"task_id": task_id})
        assert ds_after is not None
        assert ds_after["status"] == "completed"
        print(f"[OK] Dataset created: '{ds_after['name']}', record_count: {ds_after['record_count']}")

        records_count = await db.dataset_records.count_documents({"dataset_id": str(ds_after["_id"])})
        assert records_count == ds_after["record_count"]
        assert records_count <= limit
        print(f"[OK] Dataset records verified in MongoDB ({records_count} records <= limit {limit})")

        # 7. Test Idempotency: executing completed task again
        idempotent_res = await executor.execute(task_id)
        assert idempotent_res["status"] == "already_completed"
        print(f"[OK] Idempotency verified: duplicate execution returned '{idempotent_res['status']}'")

    print("\n==================================================")
    print("RUNNING FAILURE AND EDGE CASE TESTS")
    print("==================================================")

    # Test Invalid Task ID
    try:
        await executor.execute("invalid_task_id_xyz")
        assert False, "Should fail on invalid task ID"
    except WorkflowExecutorError as exc:
        print(f"[OK] Invalid task ID rejected: {exc}")

    # Test Task without AI plan
    unplanned_task = await task_service.create_task(prompt="Unplanned task", record_limit=10)
    unplanned_id = unplanned_task["id"]
    try:
        await executor.execute(unplanned_id)
        assert False, "Should fail on unplanned task"
    except WorkflowExecutorError as exc:
        print(f"[OK] Unplanned task execution rejected: {exc}")

    print("\nALL PHASE 4 PROMPT 4 INTEGRATION TESTS PASSED SUCCESSFULLY!")
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(run_scenario_tests())
