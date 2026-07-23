import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.main import app
from backend.app.core.database import Base, get_db

# Create in-memory SQLite DB for clean testing cycles
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_temp.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_register_and_login(client):
    # Test registration
    reg_response = client.post("/api/auth/register", json={
        "email": "testuser@example.com",
        "password": "strongpassword123",
        "full_name": "Test User",
        "favorite_genres": "Sci-Fi"
    })
    assert reg_response.status_code == 200
    data = reg_response.json()
    assert data["email"] == "testuser@example.com"
    assert data["reading_streak"] == 0

    # Test login
    login_response = client.post("/api/auth/token", data={
        "username": "testuser@example.com",
        "password": "strongpassword123"
    })
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert token_data["user"]["reading_streak"] == 1

def test_recommendations_anonymous(client):
    # Retrieve recommendations for cold-start user
    rec_response = client.get("/api/recommendations/?limit=5")
    assert rec_response.status_code == 200
    recs = rec_response.json()
    assert isinstance(recs, list)

def test_rag_upload_and_query(client):
    # Mock PDF upload
    files = {"file": ("dummy.pdf", b"pdf content bytes", "application/pdf")}
    upload_response = client.post("/api/chat/rag/upload", files=files)
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    assert upload_data["status"] == "success"
    doc_id = upload_data["document_id"]

    # Mock RAG Q&A query
    query_response = client.post("/api/chat/rag/query", json={
        "document_id": doc_id,
        "query": "What are the rules?"
    })
    assert query_response.status_code == 200
    query_data = query_response.json()
    assert "answer" in query_data
    assert len(query_data["source_chunks"]) > 0
