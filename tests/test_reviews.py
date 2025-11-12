from tests.utils import client
from datetime import datetime


def test_post_and_get_reviews():
    # post a review
    resp = client.post("/reviews", json={"author": "Alice", "text": "Great app", "rating": 5})
    assert resp.status_code == 201
    data = resp.json()
    assert data["author"] == "Alice"
    assert data["text"] == "Great app"
    assert data["rating"] == 5

    # fetch reviews
    resp2 = client.get("/reviews")
    assert resp2.status_code == 200
    items = resp2.json()
    assert any(r["id"] == data["id"] for r in items)
