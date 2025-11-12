from fastapi.testclient import TestClient
from src.api_fastapi import app

client = TestClient(app)
