from fastapi import FastAPI, HTTPException
from typing import Dict

app = FastAPI()


@app.get("/health")
def health() -> Dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}


@app.get("/items/{item_id}")
def read_item(item_id: int):
    """Example endpoint returning a simple item by id."""
    if item_id < 0:
        raise HTTPException(status_code=400, detail="Invalid item id")
    return {"id": item_id, "name": f"item-{item_id}"}
