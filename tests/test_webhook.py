import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_webhook_endpoint():
    """Test Dialogflow webhook endpoint."""
    # Mock Dialogflow request
    dialogflow_request = {
        "responseId": "test-response-id",
        "queryResult": {
            "queryText": "analyze key rate",
            "parameters": {},
            "allRequiredParamsPresent": True,
            "fulfillmentText": "",
            "fulfillmentMessages": [],
            "outputContexts": [],
            "intent": {
                "name": "projects/test-project/agent/intents/test-intent",
                "displayName": "AnalyzeKeyRate"
            },
            "intentDetectionConfidence": 1.0,
            "diagnosticInfo": {},
            "languageCode": "ru"
        },
        "originalDetectIntentRequest": {},
        "session": "projects/test-project/agent/sessions/test-session"
    }

    response = client.post("/dialogflow-webhook", json=dialogflow_request)
    assert response.status_code == 200
    data = response.json()
    assert "fulfillmentText" in data

def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "CBR Analysis System MVP" in data["message"]
