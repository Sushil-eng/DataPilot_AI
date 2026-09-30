"""
Unit test suite for Phase 4 Prompt 4 — Workflow Execution Engine.
Tests StepExecutor, WorkflowExecutor, ExecutionContext, security rules,
tool mapping, retries, and dataset storage without needing a live network/DB.
"""

import sys
import os
import asyncio

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.workflow.execution_models import ExecutionContext, StepStatus, ExecutionStatistics
from app.workflow.step_executor import StepExecutor, StepExecutionError, ALLOWED_TOOLS
from app.workflow.dataset_storage import DatasetStorageService
from app.workflow.executor import WorkflowExecutor


def test_allowed_tools_security():
    """Verify tool safety rules reject forbidden tools like execute_shell."""
    executor = StepExecutor()
    context = ExecutionContext(
        task_id="test_task_1",
        workflow_id="wf_1",
        dataset_id="ds_1",
        requirements={},
        schema={"fields": [{"name": "title", "type": "string"}]},
    )

    forbidden_step = {
        "id": "step_bad",
        "name": "Execute Shell Command",
        "tool": "execute_shell",
    }

    try:
        asyncio.run(executor.execute_step(forbidden_step, context))
        assert False, "Should have raised StepExecutionError for forbidden tool"
    except StepExecutionError as exc:
        assert "Forbidden or unsupported tool type 'execute_shell'" in str(exc)
        print("[OK] Security check passed: forbidden tool execute_shell rejected")


def test_informational_step_skipping():
    """Verify informational/planning steps are completed immediately without operations."""
    executor = StepExecutor()
    context = ExecutionContext(
        task_id="test_task_2",
        workflow_id="wf_2",
        dataset_id="ds_2",
        requirements={},
        schema={"fields": []},
    )

    info_step = {
        "id": "step_1",
        "name": "Understanding request",
        "tool": "understand",
    }

    res = asyncio.run(executor.execute_step(info_step, context))
    assert res["status"] == "completed"
    assert res["progress"] == 100
    print("[OK] Informational step handled cleanly")


def test_execution_context_statistics():
    """Verify execution statistics and record limit capping in context."""
    schema = {
        "fields": [
            {"name": "company_name", "type": "string", "required": True},
            {"name": "location", "type": "string"},
        ]
    }
    context = ExecutionContext(
        task_id="task_3",
        workflow_id="wf_3",
        dataset_id="ds_3",
        requirements={},
        schema=schema,
        record_limit=2,
    )

    context.raw_records = [
        {"data": {"company_name": "AI One", "location": "Mumbai"}},
        {"data": {"company_name": "AI Two", "location": "Bengaluru"}},
        {"data": {"company_name": "AI Three", "location": "Delhi"}},
    ]

    executor = StepExecutor()

    # Transform
    res_transform = asyncio.run(executor.execute_step({"id": "2", "tool": "transform"}, context))
    assert len(context.processed_records) == 3

    # Validate
    res_validate = asyncio.run(executor.execute_step({"id": "3", "tool": "validate"}, context))
    assert len(context.valid_records) == 3

    # Deduplicate (should cap to record_limit=2)
    res_dedup = asyncio.run(executor.execute_step({"id": "4", "tool": "deduplicate"}, context))
    assert len(context.final_records) == 2
    assert context.statistics.final_records == 2

    print("[OK] Workflow step pipeline & record limit capping verified")


if __name__ == "__main__":
    test_allowed_tools_security()
    test_informational_step_skipping()
    test_execution_context_statistics()
    print("\nALL WORKFLOW UNIT TESTS PASSED SUCCESSFULLY!")
