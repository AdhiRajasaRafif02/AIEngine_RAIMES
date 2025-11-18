from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from .service.api_gemini import analyze_mining_questionnaire

app = FastAPI(title="AIEngine RAIMES", description="Mining Evaluation System API")

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

class QuestionnaireAnalysis(BaseModel):
    analysis: str
    score: int = Field(..., ge=1, le=100)
    evaluation_date: datetime

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

@app.post("/analyze-mining-questionnaire", response_model=QuestionnaireAnalysis)
async def analyze_questionnaire(
    questionnaire_answers: str = Form(..., description="JSON string berisi jawaban kuisioner mining evaluation"),
    supporting_file: Optional[UploadFile] = File(None, description="File pendukung (PDF, DOC, TXT, dll)")
):
    """Analisis jawaban kuisioner mining evaluation system menggunakan Gemini AI.
    
    Parameters:
    - questionnaire_answers: String JSON berisi jawaban kuisioner
    - supporting_file: File pendukung optional untuk analisis tambahan
    
    Returns:
    - Hasil analisis dengan skor 1-100
    """
    try:
        # Baca file pendukung jika ada
        file_content = None
        file_name = None
        if supporting_file:
            file_content = await supporting_file.read()
            file_name = supporting_file.filename
        
        # Panggil fungsi analisis dari api_gemini
        result = await analyze_mining_questionnaire(
            questionnaire_answers=questionnaire_answers,
            supporting_file_content=file_content,
            supporting_file_name=file_name
        )
        
        return QuestionnaireAnalysis(
            analysis=result["analysis"],
            score=result["score"],
            evaluation_date=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error dalam analisis kuisioner: {str(e)}"
        )

# Simple in-memory store for reviews (resets on process restart)
_reviews: List[Review] = []
_next_id = 1


@app.get("/reviews", response_model=List[Review])
def list_reviews():
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
