from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from backend.app.core.database import get_db
from backend.app.models.models import Book, Rating, Review, Bookmark, ReadingHistory, User, WishlistItem, ReviewLike, ReviewComment, followers_association
from backend.app.api.auth import get_current_user

router = APIRouter(prefix="/api/books", tags=["Books & Catalog"])

# Pydantic Schemas
class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    publisher: Optional[str]
    isbn: Optional[str]
    image_url_s: Optional[str]
    image_url_m: Optional[str]
    image_url_l: Optional[str]
    description: Optional[str]
    genres: Optional[str]
    rating_avg: float
    rating_count: int

    class Config:
        from_attributes = True

class ReviewCreate(BaseModel):
    review_text: str
    rating: Optional[float] = None

class CommentCreate(BaseModel):
    comment_text: str

class CommentResponse(BaseModel):
    id: int
    review_id: int
    user_id: int
    user_name: str
    comment_text: str
    created_at: datetime

    class Config:
        from_attributes = True

class ReviewResponse(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str]
    review_text: str
    rating: Optional[float]
    likes_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class BookmarkResponse(BaseModel):
    book_id: int
    title: str
    author: str
    image_url: str

    class Config:
        from_attributes = True

class WishlistResponse(BaseModel):
    book_id: int
    title: str
    author: str
    image_url: str

    class Config:
        from_attributes = True

class ReadingHistoryUpdate(BaseModel):
    progress: int # 0 to 100
    reading_time_minutes: Optional[int] = 0

class ReadingHistoryResponse(BaseModel):
    book_id: int
    title: str
    author: str
    image_url: str
    progress: int
    status: str
    last_read_at: datetime

    class Config:
        from_attributes = True

class PublicProfileResponse(BaseModel):
    id: int
    full_name: Optional[str]
    xp_points: int
    reading_streak: int
    badges: str
    favorite_genres: str

    class Config:
        from_attributes = True

# Helper to reward XP
def reward_xp(user: User, amount: int, db: Session):
    user.xp_points += amount
    # Check Badge Triggers
    user_badges = [b.strip() for b in user.badges.split(",") if b.strip()]
    if user.xp_points >= 100 and "bronze_member" not in user_badges:
        user_badges.append("bronze_member")
    if user.xp_points >= 500 and "silver_member" not in user_badges:
        user_badges.append("silver_member")
    if user.xp_points >= 1000 and "gold_member" not in user_badges:
        user_badges.append("gold_member")
    if user.reading_streak >= 7 and "streak_week" not in user_badges:
        user_badges.append("streak_week")
    user.badges = ",".join(user_badges)
    db.commit()

# Get Top 50 Popular Books
@router.get("/popular", response_model=List[BookResponse])
def get_popular_books(db: Session = Depends(get_db)):
    return db.query(Book).order_by(Book.rating_count.desc(), Book.rating_avg.desc()).limit(50).all()

# Get paginated books list
@router.get("/", response_model=List[BookResponse])
def get_books(
    skip: int = 0,
    limit: int = 20,
    author: Optional[str] = None,
    genre: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Book)
    if author:
        query = query.filter(Book.author.ilike(f"%{author}%"))
    if genre:
        query = query.filter(Book.genres.ilike(f"%{genre}%"))
    return query.offset(skip).limit(limit).all()

# Get specific book details
@router.get("/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

# Create review for a book
@router.post("/{book_id}/reviews", response_model=ReviewResponse)
def add_review(
    book_id: int,
    review_in: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    review = Review(
        user_id=current_user.id,
        book_id=book_id,
        review_text=review_in.review_text,
        rating=review_in.rating
    )
    db.add(review)
    
    if review_in.rating is not None:
        rating = Rating(
            user_id=current_user.id,
            book_id=book_id,
            rating=review_in.rating
        )
        db.add(rating)
        db.commit()
        
        # Recalculate book average rating
        ratings = db.query(Rating).filter(Rating.book_id == book_id).all()
        avg = sum([r.rating for r in ratings]) / len(ratings)
        book.rating_avg = round(avg, 2)
        book.rating_count = len(ratings)

    reward_xp(current_user, 15, db) # Reward XP for adding review
    db.commit()
    db.refresh(review)
    
    return ReviewResponse(
        id=review.id,
        user_id=review.user_id,
        user_name=current_user.full_name or current_user.email,
        review_text=review.review_text,
        rating=review.rating,
        likes_count=0,
        created_at=review.created_at
    )

# Get all reviews for a book
@router.get("/{book_id}/reviews", response_model=List[ReviewResponse])
def get_book_reviews(book_id: int, db: Session = Depends(get_db)):
    reviews = db.query(Review).filter(Review.book_id == book_id).all()
    results = []
    for r in reviews:
        user = db.query(User).filter(User.id == r.user_id).first()
        likes_count = db.query(ReviewLike).filter(ReviewLike.review_id == r.id).count()
        results.append(ReviewResponse(
            id=r.id,
            user_id=r.user_id,
            user_name=user.full_name or user.email if user else "Anonymous",
            review_text=r.review_text,
            rating=r.rating,
            likes_count=likes_count,
            created_at=r.created_at
        ))
    return results

# Like a review
@router.post("/reviews/{review_id}/like")
def like_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    existing_like = db.query(ReviewLike).filter(
        ReviewLike.review_id == review_id,
        ReviewLike.user_id == current_user.id
    ).first()
    
    if existing_like:
        db.delete(existing_like)
        db.commit()
        return {"status": "unliked", "message": "Review unliked"}
    else:
        new_like = ReviewLike(review_id=review_id, user_id=current_user.id)
        db.add(new_like)
        reward_xp(current_user, 5, db) # reward liker
        db.commit()
        return {"status": "liked", "message": "Review liked"}

# Comment on a review
@router.post("/reviews/{review_id}/comments", response_model=CommentResponse)
def add_review_comment(
    review_id: int,
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    comment = ReviewComment(
        review_id=review_id,
        user_id=current_user.id,
        comment_text=comment_in.comment_text
    )
    db.add(comment)
    reward_xp(current_user, 10, db)
    db.commit()
    db.refresh(comment)
    
    return CommentResponse(
        id=comment.id,
        review_id=comment.review_id,
        user_id=comment.user_id,
        user_name=current_user.full_name or current_user.email,
        comment_text=comment.comment_text,
        created_at=comment.created_at
    )

# Get review comments
@router.get("/reviews/{review_id}/comments", response_model=List[CommentResponse])
def get_review_comments(review_id: int, db: Session = Depends(get_db)):
    comments = db.query(ReviewComment).filter(ReviewComment.review_id == review_id).all()
    results = []
    for c in comments:
        user = db.query(User).filter(User.id == c.user_id).first()
        results.append(CommentResponse(
            id=c.id,
            review_id=c.review_id,
            user_id=c.user_id,
            user_name=user.full_name or user.email if user else "Anonymous",
            comment_text=c.comment_text,
            created_at=c.created_at
        ))
    return results

# Toggle bookmarking state
@router.post("/{book_id}/bookmark")
def toggle_bookmark(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    bookmark = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.book_id == book_id
    ).first()
    
    if bookmark:
        db.delete(bookmark)
        db.commit()
        return {"status": "removed", "message": "Book removed from bookmarks"}
    else:
        new_bookmark = Bookmark(user_id=current_user.id, book_id=book_id)
        db.add(new_bookmark)
        reward_xp(current_user, 10, db)
        db.commit()
        return {"status": "bookmarked", "message": "Book added to bookmarks"}

# Get user bookmarks
@router.get("/bookmarks/me", response_model=List[BookmarkResponse])
def get_my_bookmarks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bookmarks = db.query(Bookmark).filter(Bookmark.user_id == current_user.id).all()
    result = []
    for bm in bookmarks:
        book = db.query(Book).filter(Book.id == bm.book_id).first()
        if book:
            result.append(BookmarkResponse(
                book_id=book.id,
                title=book.title,
                author=book.author,
                image_url=book.image_url_m or ""
            ))
    return result

# Toggle wishlist state
@router.post("/{book_id}/wishlist")
def toggle_wishlist(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    wish = db.query(WishlistItem).filter(
        WishlistItem.user_id == current_user.id,
        WishlistItem.book_id == book_id
    ).first()
    
    if wish:
        db.delete(wish)
        db.commit()
        return {"status": "removed", "message": "Book removed from wishlist"}
    else:
        new_wish = WishlistItem(user_id=current_user.id, book_id=book_id)
        db.add(new_wish)
        db.commit()
        return {"status": "added", "message": "Book added to wishlist"}

# Get wishlist
@router.get("/wishlist/me", response_model=List[WishlistResponse])
def get_my_wishlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    wishlist = db.query(WishlistItem).filter(WishlistItem.user_id == current_user.id).all()
    result = []
    for wi in wishlist:
        book = db.query(Book).filter(Book.id == wi.book_id).first()
        if book:
            result.append(WishlistResponse(
                book_id=book.id,
                title=book.title,
                author=book.author,
                image_url=book.image_url_m or ""
            ))
    return result

# Update reading progress
@router.post("/{book_id}/history", response_model=ReadingHistoryResponse)
def update_reading_progress(
    book_id: int,
    history_in: ReadingHistoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    history = db.query(ReadingHistory).filter(
        ReadingHistory.user_id == current_user.id,
        ReadingHistory.book_id == book_id
    ).first()
    
    original_status = None
    if history:
        original_status = history.status
        history.progress = history_in.progress
        history.reading_time_minutes += history_in.reading_time_minutes
        if history_in.progress >= 100:
            history.status = "completed"
    else:
        status_val = "completed" if history_in.progress >= 100 else "reading"
        history = ReadingHistory(
            user_id=current_user.id,
            book_id=book_id,
            progress=history_in.progress,
            status=status_val,
            reading_time_minutes=history_in.reading_time_minutes
        )
        db.add(history)
        
    db.commit()
    
    # Award XP for completions
    if history.status == "completed" and original_status != "completed":
        reward_xp(current_user, 50, db)
    else:
        reward_xp(current_user, 5, db)

    db.refresh(history)
    
    return ReadingHistoryResponse(
        book_id=book.id,
        title=book.title,
        author=book.author,
        image_url=book.image_url_m or "",
        progress=history.progress,
        status=history.status,
        last_read_at=history.last_read_at
    )

# Get reading history
@router.get("/history/me", response_model=List[ReadingHistoryResponse])
def get_my_reading_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    histories = db.query(ReadingHistory).filter(ReadingHistory.user_id == current_user.id).all()
    result = []
    for h in histories:
        book = db.query(Book).filter(Book.id == h.book_id).first()
        if book:
            result.append(ReadingHistoryResponse(
                book_id=book.id,
                title=book.title,
                author=book.author,
                image_url=book.image_url_m or "",
                progress=h.progress,
                status=h.status,
                last_read_at=h.last_read_at
            ))
    return result

# Toggle Social Follow
@router.post("/social/follow/{target_user_id}")
def toggle_follow(
    target_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if target_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    is_following = db.query(followers_association).filter(
        followers_association.c.follower_id == current_user.id,
        followers_association.c.following_id == target_user_id
    ).first()
    
    if is_following:
        db.execute(followers_association.delete().where(
            followers_association.c.follower_id == current_user.id
        ).where(
            followers_association.c.following_id == target_user_id
        ))
        db.commit()
        return {"status": "unfollowed", "message": f"You unfollowed {target_user.full_name or target_user.email}"}
    else:
        db.execute(followers_association.insert().values(
            follower_id=current_user.id,
            following_id=target_user_id
        ))
        db.commit()
        return {"status": "followed", "message": f"You are now following {target_user.full_name or target_user.email}"}

# Get User Profile details
@router.get("/social/profile/{target_user_id}", response_model=PublicProfileResponse)
def get_user_profile(target_user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
