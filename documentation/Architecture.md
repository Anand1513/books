# NextGen Reads AI - System & Architecture Documentation

NextGen Reads AI is an enterprise-grade AI-powered Book Recommendation Platform built on microservice principles with FastAPI and Next.js.

---

## 1. System Architecture Diagram

```mermaid
graph TD
    Client[Next.js Frontend Client] -->|HTTP / JSON| API_Gateway[Nginx Reverse Proxy / Gateway]
    API_Gateway -->|Route /api| FastAPI[FastAPI Application Server]
    FastAPI -->|JWT / OAuth Auth| AuthService[Auth API Module]
    FastAPI -->|Fetch Catalog| BookService[Book API Module]
    FastAPI -->|Compute Recs| RecommendationService[Hybrid Recommendation pipeline]
    FastAPI -->|Parse PDFs / Chat| LLMService[FastAPI RAG/LLM Service]
    
    RecommendationService -->|Item Similarity Weights| SimPickle[(similarity_scores.pkl)]
    RecommendationService -->|Popularity Thresholds| PopPickle[(popular.pkl)]
    
    FastAPI -->|Query Relational Data| SQLiteDB[(SQLite / PostgreSQL Database)]
    FastAPI -->|Cache / Rate Limit| RedisCache[(Redis Cache Store)]
    LLMService -->|Semantic Vector Match| FAISSIndex[(FAISS Vector Database)]
```

---

## 2. Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    User ||--o{ Rating : "submits"
    User ||--o{ Review : "posts"
    User ||--o{ Bookmark : "creates"
    User ||--o{ ReadingHistory : "has"
    User ||--o{ RecommendationFeedback : "sends"
    Book ||--o{ Rating : "receives"
    Book ||--o{ Review : "receives"
    Book ||--o{ Bookmark : "assigned"
    Book ||--o{ ReadingHistory : "assigned"
    
    User {
        int id PK
        string email
        string hashed_password
        string full_name
        string role
        int reading_streak
        int xp_points
        string badges
        string favorite_genres
        int reading_challenge_count
        datetime created_at
    }
    
    Book {
        int id PK
        string title
        string author
        string publisher
        string isbn
        string image_url_m
        string genres
        float rating_avg
        int rating_count
    }
    
    Rating {
        int id PK
        int user_id FK
        int book_id FK
        float rating
        datetime created_at
    }
    
    Review {
        int id PK
        int user_id FK
        int book_id FK
        string review_text
        float rating
        datetime created_at
    }
```

---

## 3. Recommendation Pipeline Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI Router
    participant Hybrid as HybridRecommender (ml/pipeline.py)
    participant DB as SQLite Database
    
    Client->>API: GET /api/recommendations/ (with JWT & session context)
    API->>DB: Query user ratings history (if auth token valid)
    DB-->>API: Return user read & rated list
    API->>Hybrid: get_recommendations(user_id, session_context)
    
    Note over Hybrid: Step 1: Filter globally trending books (Popularity)
    Note over Hybrid: Step 2: Compute item-item weights (Collaborative Filtering)
    Note over Hybrid: Step 3: Filter matching author overlaps (Content-Based)
    Note over Hybrid: Step 4: Calculate query-title string overlap (Semantic Sim)
    Note over Hybrid: Step 5: Weigh scores and simulate LLM Reranking
    
    Hybrid-->>API: Return top sorted recommendation payloads + Explainability metadata
    API-->>Client: Return JSON array containing confidence, genre match, and reader overlap scores
```

---

## 4. API Documentation

| Endpoint | Method | Authentication | Description |
|---|---|---|---|
| `/api/auth/register` | POST | None | Create a new user profile with favorite genres. |
| `/api/auth/token` | POST | None | Verify password credentials and retrieve JWT token. |
| `/api/auth/me` | GET | JWT | Fetch authenticated user's profile details. |
| `/api/books/` | GET | None | Get paginated book catalog list, filterable by genre/author. |
| `/api/books/{id}/reviews` | POST | JWT | Add a text review and rating, incrementing user XP. |
| `/api/recommendations/` | GET | Optional JWT | Retrieve hybrid personalized list containing confidence explanations. |
| `/api/chat/` | POST | JWT | Conversational interface with AI reading coach. |
| `/api/chat/rag/upload` | POST | None | Upload PDF summary, parse content, and index vectors. |
| `/api/chat/rag/query` | POST | None | Query vectorized PDF context. |
| `/api/analytics/dashboard` | GET | JWT | Fetch MAU, DAU, and CTR stats for charts. |

---

## 5. Deployment Guide

### Requirements
- Docker & Docker Compose
- Node.js (v20+) & npm
- Python (v3.12+)

### Running Locally with Docker Compose
1. Navigate to the deployment folder:
   ```bash
   cd deployment
   ```
2. Start all microservices in the background:
   ```bash
   docker-compose up --build -d
   ```
3. The platform will be active on:
   - Next.js Client: `http://localhost:3000`
   - FastAPI swagger: `http://localhost:8000/docs`
   - Nginx server proxy: `http://localhost:80`
