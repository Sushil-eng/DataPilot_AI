import sys
import asyncio
from fastapi.testclient import TestClient
from app.main import app

def run_tests():
    with TestClient(app) as client:
        print("--- 1. Testing GET / ---")
        r1 = client.get("/")
        print("Status:", r1.status_code)
        print("Response:", r1.json())
        assert r1.status_code == 200
        assert r1.json().get("status") == "ok"
        
        print("\n--- 2. Testing GET /api/health ---")
        r2 = client.get("/api/health")
        print("Status:", r2.status_code)
        print("Response:", r2.json())
        assert r2.status_code == 200
        assert r2.json().get("status") in ["ok", "healthy"]
        assert "database" in r2.json()
        
        print("\n--- 3. Testing GET /docs ---")
        r3 = client.get("/docs")
        print("Status:", r3.status_code)
        assert r3.status_code == 200
        
        print("\n--- 4. Testing POST /api/auth/login with invalid payload ---")
        r4 = client.post("/api/auth/login", json={"email": "nonexistent@example.com", "password": "wrong"})
        print("Status:", r4.status_code)
        print("Response:", r4.json())
        assert r4.status_code == 401
        
        print("\n--- All Backend Endpoints Verified Successfully! ---")

if __name__ == "__main__":
    run_tests()
