"""
Comprehensive Test Suite for Source Fetching & Browser Fallback System

Tests scenarios A–F as specified:
  A. Accessible normal website
  B. 403 website
  C. JavaScript-heavy website
  D. Timeout website
  E. Invalid URL
  F. Multiple sources where some fail
"""

import asyncio
import logging
import sys
import os

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("test_fetcher_matrix")


async def run_tests():
    from app.collection.fetcher import SourceFetcher, HTTPFetcher, BrowserFetcher
    from app.workflow.execution_models import ExecutionContext
    from app.workflow.step_executor import StepExecutor, StepExecutionError

    fetcher = SourceFetcher()
    results_matrix = {}

    print("\n==================================================")
    print("1. TEST A: Accessible normal website")
    print("==================================================")
    url_a = "https://httpbin.org/html"
    res_a = await fetcher.fetch(url_a)
    print(f"URL: {url_a}")
    print(f"Status: {res_a.get('status')}")
    print(f"HTTP Status: {res_a.get('http_status')}")
    print(f"Title: {res_a.get('title')}")
    print(f"Fetcher Type: {res_a.get('fetcher_type')}")
    results_matrix['A'] = res_a.get('status') == 'fetched' and res_a.get('http_status') == 200

    print("\n==================================================")
    print("2. TEST B: 403 Website (HTTP 403 / Browser Fallback)")
    print("==================================================")
    url_b = "https://gadgets360.com"
    res_b = await fetcher.fetch(url_b)
    print(f"URL: {url_b}")
    print(f"Status: {res_b.get('status')}")
    print(f"HTTP Status: {res_b.get('http_status')}")
    print(f"Error: {res_b.get('error')}")
    print(f"Fetcher Type: {res_b.get('fetcher_type')}")
    results_matrix['B'] = res_b.get('status') in ('blocked', 'fetched') or res_b.get('http_status') in (403, 200)

    print("\n==================================================")
    print("3. TEST C: JavaScript-heavy Website")
    print("==================================================")
    url_c = "https://react.dev"
    res_c = await fetcher.fetch(url_c)
    print(f"URL: {url_c}")
    print(f"Status: {res_c.get('status')}")
    print(f"HTTP Status: {res_c.get('http_status')}")
    print(f"Title: {res_c.get('title')}")
    print(f"Fetcher Type: {res_c.get('fetcher_type')}")
    results_matrix['C'] = res_c.get('status') == 'fetched' and res_c.get('http_status') == 200

    print("\n==================================================")
    print("4. TEST D: Timeout Website")
    print("==================================================")
    # 10.255.255.1 is non-routable IP that times out
    url_d = "http://10.255.255.1"
    res_d = await fetcher.fetch(url_d)
    print(f"URL: {url_d}")
    print(f"Status: {res_d.get('status')}")
    print(f"HTTP Status: {res_d.get('http_status')}")
    print(f"Error: {res_d.get('error')}")
    results_matrix['D'] = res_d.get('status') in ('timeout', 'failed')

    print("\n==================================================")
    print("5. TEST E: Invalid URL / SSRF Target")
    print("==================================================")
    url_e = "http://localhost:8000/internal"
    res_e = await fetcher.fetch(url_e)
    print(f"URL: {url_e}")
    print(f"Status: {res_e.get('status')}")
    print(f"HTTP Status: {res_e.get('http_status')}")
    print(f"Error: {res_e.get('error')}")
    results_matrix['E'] = res_e.get('status') == 'failed' and res_e.get('http_status') == 400

    print("\n==================================================")
    print("6. TEST F: Multiple sources where some fail (Batch Execution)")
    print("==================================================")
    sources_f = [
        {"url": "https://httpbin.org/html", "id": "src_1"},
        {"url": "https://httpbin.org/json", "id": "src_2"},
        {"url": "https://gadgets360.com", "id": "src_3"},
        {"url": "https://quora.com", "id": "src_4"},
        {"url": "http://10.255.255.1", "id": "src_5"},
        {"url": "http://localhost/admin", "id": "src_6"},
        {"url": "https://httpbin.org/xml", "id": "src_7"},
        {"url": "https://example.com", "id": "src_8"},
        {"url": "https://httpbin.org/robots.txt", "id": "src_9"},
        {"url": "https://gadgetsnow.indiatimes.com", "id": "src_10"},
    ]

    context = ExecutionContext(
        task_id="test_task_001",
        workflow_id="test_wf_001",
        dataset_id="test_ds_001",
        requirements={"intent": "Product Search", "goal": "Test batch resilience"},
        schema={
            "fields": [
                {"name": "title", "type": "string", "required": True},
                {"name": "content", "type": "string", "required": False},
            ]
        },
        record_limit=10,
    )
    context.sources = sources_f

    executor = StepExecutor()
    extract_output = await executor._execute_extract(context)

    print("\nStep Extract Execution Result:")
    print(f"Total Sources Discovered: {extract_output['sources_total']}")
    print(f"Sources Processed (Usable): {extract_output['sources_processed']}")
    print(f"Sources Blocked: {extract_output['sources_blocked']}")
    print(f"Sources Timeout: {extract_output['sources_timeout']}")
    print(f"Sources Failed: {extract_output['sources_failed']}")
    print(f"Records Extracted: {extract_output['records_extracted']}")

    print("\nSource Details Sample:")
    for detail in extract_output.get("source_details", []):
        print(f"  - {detail.get('url')} -> status: {detail.get('status')} | error: {detail.get('error')}")

    results_matrix['F'] = (
        extract_output['sources_processed'] > 0 and
        (extract_output['sources_blocked'] > 0 or extract_output['sources_failed'] > 0) and
        len(context.raw_records) == extract_output['records_extracted']
    )

    print("\n==================================================")
    print("TEST MATRIX RESULTS:")
    print("==================================================")
    all_passed = True
    for test_name, passed in results_matrix.items():
        status_str = "PASSED" if passed else "FAILED"
        print(f"  Test {test_name}: {status_str}")
        if not passed:
            all_passed = False

    print(f"\nOVERALL RESULT: {'ALL PASSED' if all_passed else 'SOME TESTS FAILED'}")


if __name__ == "__main__":
    asyncio.run(run_tests())
