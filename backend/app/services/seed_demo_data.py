"""
Demo Data Seeder
Populates MongoDB with generic development/demo data.
Run: python -m app.services.seed_demo_data
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from app.database.connection import connect_to_mongo, close_mongo_connection, get_db
from app.schemas import DEFAULT_WORKFLOW_STEPS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================================================
# DEMO TASKS (Generic — NOT job-specific)
# ==================================================
DEMO_TASKS = [
    {
        "prompt": "Find 50 AI startups in Mumbai with funding details",
        "record_limit": 50,
        "status": "completed",
        "progress": 100,
        "record_count": 5,
    },
    {
        "prompt": "Collect pricing data for top 30 SaaS tools in India",
        "record_limit": 30,
        "status": "running",
        "progress": 57,
        "record_count": 3,
    },
    {
        "prompt": "Research electric vehicle manufacturers globally",
        "record_limit": 40,
        "status": "pending",
        "progress": 0,
        "record_count": 0,
    },
    {
        "prompt": "Gather contact information of 100 digital marketing agencies in Delhi",
        "record_limit": 100,
        "status": "failed",
        "progress": 28,
        "record_count": 2,
    },
    {
        "prompt": "Find open source machine learning frameworks and their GitHub stars",
        "record_limit": 25,
        "status": "completed",
        "progress": 100,
        "record_count": 4,
    },
]


# ==================================================
# DEMO DATASETS (Generic schemas for various domains)
# ==================================================
DEMO_DATASETS = [
    # Task 0 — AI Startups
    {
        "task_index": 0,
        "name": "AI Startups Directory",
        "description": "AI/ML startups in Mumbai with funding and team size",
        "schema": [
            {"name": "company_name", "type": "string"},
            {"name": "domain", "type": "string"},
            {"name": "funding_amount", "type": "number"},
            {"name": "founded_date", "type": "date"},
            {"name": "website", "type": "url"},
        ],
        "records": [
            {"company_name": "NeuralWave AI", "domain": "Computer Vision", "funding_amount": 2500000, "founded_date": "2023-03-15", "website": "https://neuralwave.ai"},
            {"company_name": "DataMind Labs", "domain": "NLP", "funding_amount": 1800000, "founded_date": "2022-11-01", "website": "https://datamindlabs.com"},
            {"company_name": "AutoML Studio", "domain": "AutoML", "funding_amount": 5000000, "founded_date": "2021-06-20", "website": "https://automlstudio.io"},
            {"company_name": "VisionTech", "domain": "Medical Imaging", "funding_amount": 3200000, "founded_date": "2024-01-10", "website": "https://visiontech.in"},
            {"company_name": "SpeakEasy AI", "domain": "Voice Assistants", "funding_amount": 900000, "founded_date": "2025-02-28", "website": "https://speakeasy.ai"},
        ],
        "sources": [
            {"url": "https://tracxn.com/explore/AI-Startups-in-Mumbai", "title": "Tracxn AI Startups Mumbai", "source_type": "web"},
            {"url": "https://crunchbase.com/hub/mumbai-ai-companies", "title": "Crunchbase Mumbai AI", "source_type": "web"},
        ],
    },
    # Task 1 — SaaS Pricing
    {
        "task_index": 1,
        "name": "SaaS Tool Pricing",
        "description": "Pricing comparison for popular SaaS tools in India",
        "schema": [
            {"name": "tool_name", "type": "string"},
            {"name": "category", "type": "string"},
            {"name": "monthly_price", "type": "number"},
            {"name": "free_tier", "type": "boolean"},
            {"name": "website", "type": "url"},
        ],
        "records": [
            {"tool_name": "SlackPro", "category": "Communication", "monthly_price": 799, "free_tier": True, "website": "https://slack.com"},
            {"tool_name": "NotionPlus", "category": "Project Management", "monthly_price": 599, "free_tier": True, "website": "https://notion.so"},
            {"tool_name": "Zoho CRM", "category": "Sales", "monthly_price": 1200, "free_tier": False, "website": "https://zoho.com/crm"},
        ],
        "sources": [
            {"url": "https://g2.com/categories/saas", "title": "G2 SaaS Categories", "source_type": "web"},
        ],
    },
    # Task 3 — Marketing Agencies
    {
        "task_index": 3,
        "name": "Digital Marketing Agencies",
        "description": "Marketing agencies in Delhi with contact info",
        "schema": [
            {"name": "agency_name", "type": "string"},
            {"name": "specialization", "type": "string"},
            {"name": "contact_email", "type": "string"},
            {"name": "website", "type": "url"},
        ],
        "records": [
            {"agency_name": "PixelForge Media", "specialization": "SEO", "contact_email": "hello@pixelforge.in", "website": "https://pixelforge.in"},
            {"agency_name": "GrowthPulse Digital", "specialization": "Performance Marketing", "contact_email": "info@growthpulse.co", "website": "https://growthpulse.co"},
        ],
        "sources": [
            {"url": "https://clutch.co/in/agencies/digital-marketing/delhi", "title": "Clutch Digital Marketing Delhi", "source_type": "web"},
            {"url": "https://api.google.com/places/v1/agencies", "title": "Google Places API", "source_type": "api"},
        ],
    },
    # Task 4 — Open Source ML Frameworks
    {
        "task_index": 4,
        "name": "ML Frameworks Comparison",
        "description": "Open source ML frameworks with GitHub stats",
        "schema": [
            {"name": "framework", "type": "string"},
            {"name": "language", "type": "string"},
            {"name": "github_stars", "type": "number"},
            {"name": "license", "type": "string"},
            {"name": "repository", "type": "url"},
        ],
        "records": [
            {"framework": "TensorFlow", "language": "Python/C++", "github_stars": 185000, "license": "Apache 2.0", "repository": "https://github.com/tensorflow/tensorflow"},
            {"framework": "PyTorch", "language": "Python/C++", "github_stars": 82000, "license": "BSD", "repository": "https://github.com/pytorch/pytorch"},
            {"framework": "scikit-learn", "language": "Python", "github_stars": 60000, "license": "BSD", "repository": "https://github.com/scikit-learn/scikit-learn"},
            {"framework": "JAX", "language": "Python", "github_stars": 30000, "license": "Apache 2.0", "repository": "https://github.com/google/jax"},
        ],
        "sources": [
            {"url": "https://github.com/topics/machine-learning", "title": "GitHub ML Topic", "source_type": "web"},
            {"url": "https://api.github.com/search/repositories?q=machine-learning", "title": "GitHub Search API", "source_type": "api"},
        ],
    },
]


def build_workflow_steps(task_status: str, task_progress: int) -> list:
    """Build workflow steps matching the task status/progress."""
    steps = [dict(s) for s in DEFAULT_WORKFLOW_STEPS]

    if task_status == "completed":
        for s in steps:
            s["status"] = "completed"
            s["result"] = {"summary": f"{s['name']} completed successfully"}
    elif task_status == "failed":
        # Complete some steps, fail on a later one
        fail_at = max(1, int(len(steps) * task_progress / 100))
        for i, s in enumerate(steps):
            if i < fail_at:
                s["status"] = "completed"
                s["result"] = {"summary": f"{s['name']} completed"}
            elif i == fail_at:
                s["status"] = "failed"
                s["result"] = {"error": f"{s['name']} encountered an error"}
            else:
                s["status"] = "pending"
    elif task_status == "running":
        running_at = max(0, int(len(steps) * task_progress / 100))
        for i, s in enumerate(steps):
            if i < running_at:
                s["status"] = "completed"
                s["result"] = {"summary": f"{s['name']} completed"}
            elif i == running_at:
                s["status"] = "running"
            else:
                s["status"] = "pending"
    # pending — all steps stay pending

    return steps


async def seed_demo_data():
    """Seed the database with generic demo data across multiple domains."""
    db = get_db()

    # Check if demo data already exists
    existing_count = await db.tasks.count_documents({})
    if existing_count > 0:
        logger.info(f"Database already has {existing_count} tasks. Skipping seeding.")
        logger.info("To re-seed, drop the database first: db.dropDatabase()")
        return

    logger.info("Seeding demo data...")
    now = datetime.now(timezone.utc)
    task_ids = []

    # Create tasks
    for i, task_def in enumerate(DEMO_TASKS):
        created_offset = timedelta(hours=len(DEMO_TASKS) - i)
        task_data = {
            "prompt": task_def["prompt"],
            "record_limit": task_def["record_limit"],
            "user_id": "default_user",
            "status": task_def["status"],
            "progress": task_def["progress"],
            "record_count": task_def["record_count"],
            "created_at": now - created_offset,
            "updated_at": now - timedelta(minutes=i * 15),
        }
        res = await db.tasks.insert_one(task_data)
        task_id = str(res.inserted_id)
        task_ids.append(task_id)
        logger.info(f"  Task {i + 1}: '{task_def['prompt'][:40]}...' → {task_id}")

    # Create workflows
    for i, task_def in enumerate(DEMO_TASKS):
        steps = build_workflow_steps(task_def["status"], task_def["progress"])
        workflow_data = {
            "task_id": task_ids[i],
            "status": task_def["status"],
            "progress": task_def["progress"],
            "steps": steps,
            "created_at": now - timedelta(hours=len(DEMO_TASKS) - i),
            "updated_at": now - timedelta(minutes=i * 15),
        }
        await db.workflows.insert_one(workflow_data)
        logger.info(f"  Workflow for Task {i + 1}: status={task_def['status']}")

    # Create datasets, records, and sources
    for ds_def in DEMO_DATASETS:
        task_idx = ds_def["task_index"]
        task_id = task_ids[task_idx]

        dataset_data = {
            "task_id": task_id,
            "name": ds_def["name"],
            "description": ds_def["description"],
            "schema": ds_def["schema"],
            "record_count": len(ds_def.get("records", [])),
            "created_at": now - timedelta(hours=len(DEMO_TASKS) - task_idx),
            "updated_at": now - timedelta(minutes=task_idx * 10),
        }
        ds_res = await db.datasets.insert_one(dataset_data)
        dataset_id = str(ds_res.inserted_id)
        logger.info(f"  Dataset: '{ds_def['name']}' → {dataset_id}")

        # Insert records
        for rec in ds_def.get("records", []):
            rec_doc = {
                "dataset_id": dataset_id,
                "data": rec,
                "created_at": now - timedelta(minutes=5),
                "updated_at": now,
            }
            await db.dataset_records.insert_one(rec_doc)

        # Insert sources
        for src in ds_def.get("sources", []):
            src_doc = {
                "dataset_id": dataset_id,
                "url": src["url"],
                "title": src["title"],
                "source_type": src["source_type"],
                "collected_at": now - timedelta(minutes=10),
            }
            await db.sources.insert_one(src_doc)

    # Summary
    total_tasks = await db.tasks.count_documents({})
    total_workflows = await db.workflows.count_documents({})
    total_datasets = await db.datasets.count_documents({})
    total_records = await db.dataset_records.count_documents({})
    total_sources = await db.sources.count_documents({})

    logger.info("\n" + "=" * 50)
    logger.info("DEMO DATA SEEDED SUCCESSFULLY")
    logger.info("=" * 50)
    logger.info(f"  Tasks:     {total_tasks}")
    logger.info(f"  Workflows: {total_workflows}")
    logger.info(f"  Datasets:  {total_datasets}")
    logger.info(f"  Records:   {total_records}")
    logger.info(f"  Sources:   {total_sources}")
    logger.info("=" * 50)


async def main():
    await connect_to_mongo()
    try:
        await seed_demo_data()
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
