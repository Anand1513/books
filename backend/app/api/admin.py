from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from backend.app.core.database import get_db
from backend.app.models.models import Book, User, Review
from backend.app.api.auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["Admin & Moderation"])

class BookCreate(BaseModel):
    title: str
    author: str
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    genres: Optional[str] = "Fiction"
    image_url_m: Optional[str] = None
    description: Optional[str] = None

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    genres: Optional[str] = None
    description: Optional[str] = None

class UserRoleUpdate(BaseModel):
    role: str

# Helper dependency to verify Admin role
def verify_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin permissions required")
    return current_user

# Get list of all users (admin only)
@router.get("/users", response_model=List[dict])
def list_users(db: Session = Depends(get_db), admin: User = Depends(verify_admin)):
    users = db.query(User).all()
    return [{"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role, "xp_points": u.xp_points} for u in users]

# Update user role (admin only)
@router.put("/users/{user_id}/role")
def update_user_role(user_id: int, role_in: UserRoleUpdate, db: Session = Depends(get_db), admin: User = Depends(verify_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role_in.role
    db.commit()
    return {"status": "success", "message": f"User role updated to {role_in.role}"}

# Add a book to catalog
@router.post("/books")
def create_book(book_in: BookCreate, db: Session = Depends(get_db), admin: User = Depends(verify_admin)):
    existing = db.query(Book).filter(Book.isbn == book_in.isbn).first() if book_in.isbn else None
    if existing:
        raise HTTPException(status_code=400, detail="Book with this ISBN already exists")
    
    book = Book(
        title=book_in.title,
        author=book_in.author,
        publisher=book_in.publisher,
        isbn=book_in.isbn,
        genres=book_in.genres,
        image_url_m=book_in.image_url_m,
        description=book_in.description
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return {"status": "success", "book_id": book.id}

# Update a book
@router.put("/books/{book_id}")
def update_book(book_id: int, book_in: BookUpdate, db: Session = Depends(get_db), admin: User = Depends(verify_admin)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if book_in.title is not None:
        book.title = book_in.title
    if book_in.author is not None:
        book.author = book_in.author
    if book_in.publisher is not None:
        book.publisher = book_in.publisher
    if book_in.genres is not None:
        book.genres = book_in.genres
    if book_in.description is not None:
        book.description = book_in.description
        
    db.commit()
    return {"status": "success", "message": "Book catalog details updated"}

# Delete a book
@router.delete("/books/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db), admin: User = Depends(verify_admin)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(book)
    db.commit()
    return {"status": "success", "message": "Book removed from catalog"}

# Delete/moderate a review
@router.delete("/reviews/{review_id}")
def delete_review(review_id: int, db: Session = Depends(get_db), admin: User = Depends(verify_admin)):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    db.delete(review)
    db.commit()
    return {"status": "success", "message": "Review moderated and removed"}
