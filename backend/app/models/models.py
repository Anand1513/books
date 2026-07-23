from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.core.database import Base

# Association Table for Social Followers
followers_association = Table(
    "social_follows",
    Base.metadata,
    Column("follower_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("following_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, default=datetime.utcnow)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default="user") # user, admin
    
    # Gamification & Profiles
    reading_streak = Column(Integer, default=0)
    last_active_at = Column(DateTime, default=datetime.utcnow)
    badges = Column(Text, default="") # comma-separated list: "first_book, streak_3, speed_reader"
    favorite_genres = Column(Text, default="") # comma-separated list
    xp_points = Column(Integer, default=0)
    reading_challenge_count = Column(Integer, default=0) # Annual reading goal
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")
    wishlist = relationship("WishlistItem", back_populates="user", cascade="all, delete-orphan")
    history = relationship("ReadingHistory", back_populates="user", cascade="all, delete-orphan")
    feedbacks = relationship("RecommendationFeedback", back_populates="user", cascade="all, delete-orphan")
    analytics_logs = relationship("AnalyticsLog", back_populates="user", cascade="all, delete-orphan")
    
    # Social relationships
    following = relationship(
        "User",
        secondary=followers_association,
        primaryjoin=id == followers_association.c.follower_id,
        secondaryjoin=id == followers_association.c.following_id,
        backref="followers"
    )


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    author = Column(String, index=True, nullable=False)
    publisher = Column(String, nullable=True)
    isbn = Column(String, unique=True, index=True, nullable=True)
    image_url_s = Column(String, nullable=True)
    image_url_m = Column(String, nullable=True)
    image_url_l = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    genres = Column(String, default="Fiction") # Semicolon separated, e.g. "Fiction;Sci-Fi"
    rating_avg = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)

    # Relationships
    ratings = relationship("Rating", back_populates="book", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="book", cascade="all, delete-orphan")
    wishlist_items = relationship("WishlistItem", back_populates="book", cascade="all, delete-orphan")
    history = relationship("ReadingHistory", back_populates="book", cascade="all, delete-orphan")
    feedbacks = relationship("RecommendationFeedback", back_populates="book", cascade="all, delete-orphan")


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Float, nullable=False) # 1 to 5 scale
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="ratings")
    book = relationship("Book", back_populates="ratings")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    review_text = Column(Text, nullable=False)
    rating = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reviews")
    book = relationship("Book", back_populates="reviews")
    
    # Review Social Mechanics
    likes = relationship("ReviewLike", back_populates="review", cascade="all, delete-orphan")
    comments = relationship("ReviewComment", back_populates="review", cascade="all, delete-orphan")


class ReviewLike(Base):
    __tablename__ = "review_likes"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    review = relationship("Review", back_populates="likes")


class ReviewComment(Base):
    __tablename__ = "review_comments"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    comment_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    review = relationship("Review", back_populates="comments")
    user = relationship("User")


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="bookmarks")
    book = relationship("Book", back_populates="bookmarks")


class WishlistItem(Base):
    __tablename__ = "wishlist_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="wishlist")
    book = relationship("Book", back_populates="wishlist_items")


class ReadingHistory(Base):
    __tablename__ = "reading_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="reading") # "reading", "completed"
    progress = Column(Integer, default=0) # 0 to 100 percentage
    reading_time_minutes = Column(Integer, default=0)
    last_read_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="history")
    book = relationship("Book", back_populates="history")


class RecommendationFeedback(Base):
    __tablename__ = "recommendation_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    recommended_by = Column(String, nullable=False) # e.g. "hybrid_v1", "collaborative", "semantic"
    feedback_type = Column(String, nullable=False) # "click", "bookmark", "dismiss", "like", "skip"
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="feedbacks")
    book = relationship("Book", back_populates="feedbacks")


class AnalyticsLog(Base):
    __tablename__ = "analytics_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True) # None for anonymous
    event_type = Column(String, nullable=False) # "page_view", "search", "detail_view", "read_session"
    metadata_json = Column(Text, nullable=True) # extra context: query terms, duration, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="analytics_logs")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
