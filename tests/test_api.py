from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_health():
    response=client.get("/health")
    assert response.status_code==200
    assert response.json()["status"]=="ok"

def test_product_creation():
    sku="TEST-SKU-001"
    response=client.post("/products",json={
        "name":"Test Keyboard","sku":sku,"price":1499.00,"stock":10,"category":"Electronics"
    })
    assert response.status_code in (200,409)
