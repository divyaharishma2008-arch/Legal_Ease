import os

os.environ["DEMO_MODE"] = "true"
os.environ.pop("GEMINI_API_KEY", None)

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_generate_demo_document():
    payload = {
        "document_type": "Freelance Work Contract",
        "parties": "Jane Doe (Service Provider), TechNova Inc. (Client)",
        "terms": "Payment within 30 days; Confidentiality must be maintained",
        "dates": "10/04/2025",
    }

    response = client.post("/generate", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "FREELANCE WORK CONTRACT" in data["content"]
    assert "Jane Doe" in data["content"]


def test_validation_rejects_empty_document_type():
    payload = {
        "document_type": "",
        "parties": "A, B",
        "terms": "Payment within 30 days",
        "dates": "10/04/2025",
    }

    response = client.post("/generate", json=payload)
    assert response.status_code == 422
