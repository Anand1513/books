from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from backend.app.core.database import get_db
from backend.app.models.models import Book
import sys
import os

# Ensure the parent root is accessible for loading ml.indexer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from ml.indexer import SemanticIndexer

router = APIRouter(prefix="/api/search", tags=["Search Engine"])

# Initialize Semantic Search Indexer
indexer = SemanticIndexer()

# Pydantic Schemas
class BookSearchResponse(BaseModel):
    id: int
    title: str
    author: str
    image_url_m: Optional[str]
    rating_avg: float
    rating_count: int
    score: float # Similarity score for semantic search

class SuggestionResponse(BaseModel):
    title: str
    author: str

@router.get("/suggest", response_model=List[SuggestionResponse])
def get_search_suggestions(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db)
):
    # Fuzzy autocomplete search in the DB
    books = db.query(Book).filter(
        Book.title.ilike(f"%{q}%") | Book.author.ilike(f"%{q}%")
    ).limit(8).all()
    
    return [SuggestionResponse(title=b.title, author=b.author) for b in books]

@router.get("/semantic", response_model=List[BookSearchResponse])
def search_semantically(
    q: str = Query(..., min_length=3),
    limit: int = 10,
    db: Session = Depends(get_db)
):
    try:
        # Run semantic FAISS search index query
        matches = indexer.search(q, limit=limit)
        
        results = []
        for match in matches:
            title = match["title"]
            score = match["score"]
            
            # Retrieve DB details
            book = db.query(Book).filter(Book.title == title).first()
            if book:
                results.append(BookSearchResponse(
                    id=book.id,
                    title=book.title,
                    author=book.author,
                    image_url_m=book.image_url_m,
                    rating_avg=book.rating_avg,
                    rating_count=book.rating_count,
                    score=float(score)
                ))
        
        # If semantic index returns empty (e.g. not loaded/created yet), fall back to standard text filter
        if not results:
            fallback_books = db.query(Book).filter(
                Book.title.ilike(f"%{q}%") | Book.author.ilike(f"%{q}%")
            ).limit(limit).all()
            for book in fallback_books:
                results.append(BookSearchResponse(
                    id=book.id,
                    title=book.title,
                    author=book.author,
                    image_url_m=book.image_url_m,
                    rating_avg=book.rating_avg,
                    rating_count=book.rating_count,
                    score=1.0
                ))
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
