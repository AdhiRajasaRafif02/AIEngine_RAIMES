from fastapi import FastAPI, HTTPException
from typing import Dict
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class Review(BaseModel):
    id: int
    author: str
    text: str
    rating: Optional[int] = Field(None, ge=1, le=5)
    created_at: datetime


class ReviewCreate(BaseModel):
    author: str
    text: str
    rating: Optional[int] = Field(None, ge=1, le=5)

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


# Simple in-memory store for reviews (resets on process restart)
_reviews: List[Review] = []
_next_id = 1


@app.get("/reviews", response_model=List[Review])
def list_reviews():
    """Return all reviews."""
    return _reviews


@app.post("/reviews", response_model=Review, status_code=201)
def create_review(payload: ReviewCreate):
    """Create a new review and return it."""
    global _next_id
    review = Review(
        id=_next_id,
        author=payload.author,
        text=payload.text,
        rating=payload.rating,
        created_at=datetime.utcnow(),
    )
    _reviews.append(review)
    _next_id += 1
    return review
