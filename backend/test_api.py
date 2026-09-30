import urllib.request
import urllib.parse
import json
import time

base_url = "http://localhost:8000/api/tasks"

def make_request(method, url, data=None):
    req = urllib.request.Request(url, method=method)
    if data:
        data = json.dumps(data).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data=data) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTPError: {e.code} - {e.read().decode()}")
        raise

print("Waiting for server to start...")
time.sleep(2)

# Domain 1: Job
print("--- Creating Job Task ---")
job_data = {"prompt": "Find Python developer jobs in Mumbai", "record_limit": 50}
job_res = make_request("POST", base_url, job_data)
print(job_res)
job_id = job_res["data"]["id"]

# Domain 2: Company
print("--- Creating Company Task ---")
comp_data = {"prompt": "Find construction companies in Mumbai", "record_limit": 100}
comp_res = make_request("POST", base_url, comp_data)
print(comp_res)

# Domain 3: Product
print("--- Creating Product Task ---")
prod_data = {"prompt": "Compare smartphones under ₹50,000", "record_limit": 10}
prod_res = make_request("POST", base_url, prod_data)
print(prod_res)

# List Tasks
print("--- Listing Tasks ---")
list_res = make_request("GET", f"{base_url}?limit=10")
print(f"Found {len(list_res['data']['items'])} tasks")

# Get Task
print("--- Getting Task ---")
get_res = make_request("GET", f"{base_url}/{job_id}")
print(get_res)

# Update Task
print("--- Updating Task ---")
upd_data = {"status": "completed", "progress": 100, "record_count": 45}
upd_res = make_request("PATCH", f"{base_url}/{job_id}", upd_data)
print(upd_res)
verify_res = make_request("GET", f"{base_url}/{job_id}")
print(f"Updated status: {verify_res['data']['status']}")

# Delete Task
print("--- Deleting Task ---")
del_res = make_request("DELETE", f"{base_url}/{job_id}")
print(del_res)

print("ALL TESTS PASSED")
