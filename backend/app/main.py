from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pickle
import os
import sys
from backend.app.core.database import Base, engine, SessionLocal
from backend.app.models.models import Book
from backend.app.api import auth, books, recommendations, search, analytics, chat, admin

# Database setup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NextGen Reads AI API",
    description="Enterprise-grade AI Recommendation and Semantic Search Engine REST APIs.",
    version="1.0.0"
)

# CORS configurations allowing Next.js on port 3000
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5001",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router)
app.include_router(books.router)
app.include_router(recommendations.router)
app.include_router(search.router)
app.include_router(analytics.router)
app.include_router(chat.router)
app.include_router(admin.router)


def assign_genre(title: str, author: str) -> str:
    t = str(title).lower()
    a = str(author).lower()
    if any(k in t for k in ['harry potter', 'hobbit', 'lord of the rings', 'ring', 'vampire', 'witch', 'magic', 'dragon', 'wizard', 'narnia']):
        return 'Fantasy'
    if any(k in t for k in ['1984', 'dune', 'handmaid', 'galaxy', 'brave new world', 'robot', 'star', 'space', 'time', 'alien', 'fahrenheit', 'timeline']):
        return 'Sci-Fi'
    if any(k in t for k in ['habits', 'think', 'power', 'mind', 'life', 'success', 'rich', 'how to', 'guide', 'art of', 'tao']):
        return 'Self-Help'
    if any(k in t for k in ['work', 'business', 'money', 'leader', 'manage', 'exec', 'market', 'economy', 'goal']):
        return 'Productivity'
    if any(k in t for k in ['code', 'programming', 'python', 'java', 'data', 'algorithm', 'computer', 'system', 'tech']):
        return 'Computer Science'
    if any(k in t for k in ['murder', 'mystery', 'girl', 'secret', 'death', 'detective', 'crime', 'dark', 'lost']):
        return 'Mystery & Thriller'
    if any(k in t for k in ['history', 'war', 'world', 'king', 'queen', 'empire', 'revolution', 'biography', 'catcher', 'mockingbird']):
        return 'Classics'
    
    fallback_genres = ['Fiction', 'Fantasy', 'Sci-Fi', 'Classics', 'Mystery & Thriller', 'Self-Help', 'Productivity']
    return fallback_genres[hash(title) % len(fallback_genres)]

# Database seeding logic on app startup
@app.on_event("startup")
def seed_database():
    db = SessionLocal()
    try:
        book_count = db.query(Book).count()
        if book_count < 5000:
            print("Seeding books from local pickle/CSV dataset into SQL database...")
            
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            popular_pkl_path = os.path.join(base_dir, "popular.pkl")
            books_pkl_path = os.path.join(base_dir, "books.pkl")
            
            books_to_add = []
            seeded_titles = set()
            
            # Keep existing titles if re-seeding
            existing_books = db.query(Book.title).all()
            for b in existing_books:
                seeded_titles.add(b.title)
            
            if os.path.exists(popular_pkl_path):
                with open(popular_pkl_path, "rb") as f:
                    popular_df = pickle.load(f)
                    for index, row in popular_df.iterrows():
                        title = str(row["Book-Title"])
                        if title in seeded_titles:
                            continue
                        seeded_titles.add(title)
                        
                        book = Book(
                            title=title,
                            author=str(row["Book-Author"]),
                            publisher="Curated Publishers",
                            image_url_s=str(row["Image-URL-M"]),
                            image_url_m=str(row["Image-URL-M"]),
                            image_url_l=str(row["Image-URL-M"]),
                            genres=assign_genre(title, str(row["Book-Author"])),
                            rating_avg=float(row["avg_rating"]),
                            rating_count=int(row["num_ratings"]),
                            description=f"A highly acclaimed work by {row['Book-Author']}, tracking {row['num_ratings']} reader ratings with a {row['avg_rating']}/10 score."
                        )
                        books_to_add.append(book)
                        
            if os.path.exists(books_pkl_path):
                with open(books_pkl_path, "rb") as f:
                    books_df = pickle.load(f)
                    count = 0
                    for index, row in books_df.iterrows():
                        if count >= 5000:
                            break
                        title = str(row["Book-Title"])
                        if title in seeded_titles:
                            continue
                        seeded_titles.add(title)
                        
                        book = Book(
                            title=title,
                            author=str(row["Book-Author"]),
                            image_url_m=str(row["Image-URL-M"]),
                            genres=assign_genre(title, str(row["Book-Author"])),
                            rating_avg=7.5,
                            rating_count=15,
                            description=f"Explore the fascinating pages of '{title}' written by {row['Book-Author']}."
                        )
                        books_to_add.append(book)
                        count += 1
                    del books_df
                    import gc
                    gc.collect()
            
            if books_to_add:
                db.bulk_save_objects(books_to_add)
                db.commit()
                print(f"Successfully seeded {len(books_to_add)} books into SQL database.")
        else:
            print(f"Database already contains {book_count} books. Skipping seeding.")
    except Exception as e:
        print(f"Error seeding database: {e}")
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to NextGen Reads AI Enterprise APIs!"}
