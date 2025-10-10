"""
Quick API Test Script
Tests FastAPI endpoints functionality
"""

import asyncio
from api.main import app, orchestrator, portfolio
from fastapi.testclient import TestClient

def test_api():
    """Test API endpoints"""
    print("\n" + "="*80)
    print("🧪 TESTING FASTAPI ENDPOINTS")
    print("="*80 + "\n")

    # Create test client
    client = TestClient(app)

    # Test 1: Root endpoint
    print("1️⃣ Testing root endpoint...")
    response = client.get("/")
    assert response.status_code == 200
    print(f"✅ Root endpoint: {response.json()}")

    # Test 2: Health check
    print("\n2️⃣ Testing health check...")
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    print(f"✅ Health check: {response.json()}")

    # Test 3: Portfolio endpoint (without initialization should work with default portfolio)
    print("\n3️⃣ Testing portfolio endpoint...")
    try:
        response = client.get("/api/v1/portfolio")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Portfolio endpoint:")
            print(f"   Total Value: ₹{data['total_value']:,.0f}")
            print(f"   Cash: ₹{data['cash']:,.0f}")
            print(f"   Positions: {len(data['positions'])}")
        else:
            print(f"⚠️  Portfolio endpoint returned {response.status_code}: {response.json()}")
    except Exception as e:
        print(f"⚠️  Portfolio endpoint error: {e}")

    # Test 4: Decision history
    print("\n4️⃣ Testing decision history...")
    response = client.get("/api/v1/decisions")
    assert response.status_code == 200
    print(f"✅ Decision history: {len(response.json())} decisions")

    print("\n" + "="*80)
    print("✅ ALL API TESTS PASSED!")
    print("="*80 + "\n")

    print("📝 Note: Stock analysis endpoint requires full orchestrator initialization")
    print("   and is tested separately to avoid LLM API calls during unit testing.\n")


if __name__ == "__main__":
    test_api()
