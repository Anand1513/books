from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from backend.app.core.database import get_db
from backend.app.models.models import Book, RecommendationFeedback, User
from backend.app.api.auth import get_optional_current_user, get_current_user
from ml.pipeline import HybridRecommender

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations Engine"])

# Initialize Hybrid Recommender
recommender = HybridRecommender()


# Pydantic Schemas
class ExplainabilityInfo(BaseModel):
    why: str
    genre_similarity: float
    reader_overlap: float
    semantic_similarity: float
    popularity_score: float
    personalization_score: float
    confidence_score: float

class RecommendationResponse(BaseModel):
    id: int
    title: str
    author: str
    image_url_m: Optional[str]
    rating_avg: float
    rating_count: int
    explainability: ExplainabilityInfo

class FeedbackSubmit(BaseModel):
    book_id: int
    recommended_by: str # e.g. "hybrid_pipeline_v1"
    feedback_type: str # "click", "bookmark", "dismiss"

@router.get("/", response_model=List[RecommendationResponse])
def get_hybrid_recommendations(
    limit: int = 10,
    session_context: Optional[str] = Query(None, description="Comma-separated titles of books user clicked in this session"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    try:
        user_books = []
        if session_context:
            user_books = [t.strip() for t in session_context.split(",") if t.strip()]
            
        # Get recommendation names from hybrid pipeline
        recs = recommender.get_recommendations(
            user_id=current_user.id if current_user else None,
            db_session=db,
            session_books=user_books,
            limit=limit
        )
        
        results = []
        for r in recs:
            book_title = r["title"]
            explain_data = r["explain"]
            
            # Lookup in db to get real IDs and metadata
            book = db.query(Book).filter(Book.title == book_title).first()
            if book:
                results.append(RecommendationResponse(
                    id=book.id,
                    title=book.title,
                    author=book.author,
                    image_url_m=book.image_url_m,
                    rating_avg=book.rating_avg,
                    rating_count=book.rating_count,
                    explainability=ExplainabilityInfo(
                        why=explain_data["why"],
                        genre_similarity=explain_data["genre_similarity"],
                        reader_overlap=explain_data["reader_overlap"],
                        semantic_similarity=explain_data["semantic_similarity"],
                        popularity_score=explain_data["popularity_score"],
                        personalization_score=explain_data["personalization_score"],
                        confidence_score=explain_data["confidence_score"]
                    )
                ))
            else:
                b_id = abs(hash(book_title)) % 100000 + 1000
                results.append(RecommendationResponse(
                    id=b_id,
                    title=book_title,
                    author=r.get("author", "Curated Author"),
                    image_url_m=r.get("image_url", ""),
                    rating_avg=7.5,
                    rating_count=25,
                    explainability=ExplainabilityInfo(
                        why=explain_data["why"],
                        genre_similarity=explain_data["genre_similarity"],
                        reader_overlap=explain_data["reader_overlap"],
                        semantic_similarity=explain_data["semantic_similarity"],
                        popularity_score=explain_data["popularity_score"],
                        personalization_score=explain_data["personalization_score"],
                        confidence_score=explain_data["confidence_score"]
                    )
                ))
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback")
def submit_recommendation_feedback(
    feedback: FeedbackSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_feedback = RecommendationFeedback(
        user_id=current_user.id,
        book_id=feedback.book_id,
        recommended_by=feedback.recommended_by,
        feedback_type=feedback.feedback_type
    )
    db.add(db_feedback)
    db.commit()
    return {"status": "success", "message": "Recommendation feedback successfully tracked"}
