import asyncio
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath('.'))

from app.collection.fetcher import SourceFetcher
from app.workflow.step_executor import StepExecutor
from app.workflow.execution_models import ExecutionContext

async def main():
    print("=== Testing SourceFetcher & HTTPFetcher ===")
    fetcher = SourceFetcher()
    
    test_urls = [
        "https://www.naukri.com/python-developer-jobs-in-mumbai",
        "https://www.glassdoor.co.in/Job/mumbai-python-developer-jobs-SRCH_IL.0,6_IC2851180_KO7,23.htm",
        "https://in.indeed.com/q-python-developer-l-mumbai,-maharashtra-jobs.html",
        "https://www.ziprecruiter.com/Jobs/Python-Developer",
    ]
    
    for url in test_urls:
        res = await fetcher.fetch(url)
        print(f"URL: {url}")
        print(f"  Status: {res.get('status_code')} | Fetcher: {res.get('fetcher_type')} | Text len: {len(res.get('text', ''))}")
        print(f"  Error: {res.get('error')}")

    print("\n=== Testing StepExecutor Extract Resiliency ===")
    executor = StepExecutor()
    context = ExecutionContext(
        task_id="test-task-123",
        workflow_id="test-wf-123",
        dataset_id="test-ds-123",
        requirements={"goal": "Find Python jobs in Mumbai"},
        schema={"fields": [{"name": "job_title"}, {"name": "company"}, {"name": "location"}]}
    )
    context.sources = [{"id": f"src_{i}", "url": u, "metadata": {"mock": True}} for i, u in enumerate(test_urls)]
    
    result = await executor._execute_extract(context)
    print(f"Extract Result Summary: processed={result.get('sources_processed')}, records={result.get('records_extracted')}")
    print(f"Raw Records Extracted: {len(context.raw_records)}")

if __name__ == "__main__":
    asyncio.run(main())
