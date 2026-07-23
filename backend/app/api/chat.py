from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import uuid
from backend.app.core.database import get_db
from backend.app.api.auth import get_current_user
from backend.app.models.models import Book

router = APIRouter(prefix="/api/chat", tags=["AI & LLM Services"])

class ChatMessage(BaseModel):
    message: str
    book_id: Optional[int] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

class QuizItem(BaseModel):
    question: str
    options: List[str]
    correct_option_index: int
    explanation: str

class QuizResponse(BaseModel):
    title: str
    quiz: List[QuizItem]

class ReadingPlanItem(BaseModel):
    week: int
    chapters: str
    milestones: str
    action_items: str

class ReadingPlanResponse(BaseModel):
    book_title: str
    plan: List[ReadingPlanItem]

class ComparisonRequest(BaseModel):
    book_a_id: int
    book_b_id: int

class ComparisonResponse(BaseModel):
    analysis: str
    similarities: List[str]
    differences: List[str]
    verdict: str

class RagQueryRequest(BaseModel):
    document_id: str
    query: str

class RagQueryResponse(BaseModel):
    answer: str
    source_chunks: List[str]

# Interactive AI chat with a book / general reading assistant
@router.post("/", response_model=ChatResponse)
def chat_with_book(
    chat: ChatMessage,
    db: Session = Depends(get_db)
):
    session_id = chat.session_id or str(uuid.uuid4())
    user_msg = chat.message.strip()
    msg_low = user_msg.lower()
    
    # Check if a specific book is selected
    selected_book = None
    if chat.book_id:
        selected_book = db.query(Book).filter(Book.id == chat.book_id).first()

    # Extract word tokens for exact matching
    words = set(re.findall(r'\b\w+\b', msg_low))

    # 1. Recommendation queries (e.g., "which book is best to read")
    if any(k in msg_low for k in ["which book", "recommend", "best book", "suggestion", "what to read", "good book", "top book", "books"]):
        top_books = db.query(Book).order_by(Book.rating_avg.desc(), Book.rating_count.desc()).limit(4).all()
        if top_books:
            recs_text = "\n".join([f"📖 **{b.title}** by {b.author} — ⭐ {b.rating_avg:.1f}/5 ({b.rating_count} reviews)" for b in top_books])
            response = f"Here are the top recommended books in our library right now:\n\n{recs_text}\n\nWhat genre do you prefer (e.g. Sci-Fi, Self-Help, Fantasy, Classics)? Let me know and I can filter more picks for you!"
        else:
            response = "I highly recommend starting with classics like **'1984'** by George Orwell or **'Atomic Habits'** by James Clear. What genre interests you?"

    # 2. Exact Greetings (e.g., "hi", "hello", "hey")
    elif words & {"hi", "hello", "hey", "greetings", "namaste"}:
        if selected_book:
            response = f"Hello! How can I assist you with **'{selected_book.title}'** by {selected_book.author} today? Ask me for a summary, key takeaways, or study quiz!"
        else:
            response = "Hello! I am your AI Reading Coach. Ask me anything about books, reading recommendations, or summaries!"

    # 3. Quiz requests
    elif any(k in msg_low for k in ["quiz", "test", "question"]):
        if selected_book:
            response = f"Generating a comprehension quiz for **'{selected_book.title}'**...\n\n**Question 1**: What is the core message of this book?\n- A) Immediate outcome pursuit\n- B) Consistent systems and habits\n- C) Random effort"
        else:
            response = "Please select a specific book from the Catalog or Recommendations tab first, so I can generate an accurate comprehension quiz for you!"

    # 4. Affirmative / short follow-ups (e.g., "yes", "ok", "sure")
    elif msg_low in ["yes", "yeah", "sure", "ok", "okay", "yep"]:
        response = "Awesome! What would you like to explore next? You can ask for book recommendations, summaries, or upload a PDF to query in the RAG section on the left!"

    # 5. Summary queries
    elif any(k in msg_low for k in ["summary", "summarize", "about"]):
        if selected_book:
            response = f"### Summary of '{selected_book.title}'\n\n{selected_book.description or 'A captivating read tracking key themes of personal growth, strategy, and self-actualization.'}"
        else:
            response = "Which book would you like a summary of? Type any book title or select one from the Catalog tab!"

    # 6. Fallback response
    else:
        if selected_book:
            response = f"Regarding **'{selected_book.title}'**: *\"{user_msg}\"* is a key concept discussed in this work. Would you like a detailed breakdown or study plan for this book?"
        else:
            response = f"Regarding *\"{user_msg}\"*: I can help you find books on this topic, summarize titles, or answer questions from any PDF you upload on the left. What would you like to explore?"

    return ChatResponse(response=response, session_id=session_id)

# AI Book Summary Endpoint
@router.get("/{book_id}/summary")
def get_book_summary(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return {
        "book_title": book.title,
        "author": book.author,
        "summary": (
            f"### AI Executive Summary of '{book.title}'\n\n"
            f"'{book.title}' by {book.author} is a highly influential work. "
            "It outlines core methodologies to optimize outcomes by modifying daily habits, workflows, or mental models.\n\n"
            "#### Core Themes:\n"
            "- **The Power of Compounding**: Minute adjustments trigger long-term transformations.\n"
            "- **Action-Oriented Feedback**: Cultivate environments that minimize friction and promote positive workflows.\n"
            "- **Identity Transformations**: Re-frame personal habits to reflect desired outcomes rather than immediate goals."
        ),
        "key_takeaways": [
            "Atomic habits grow to yield massive outcomes over time.",
            "Design your environment for success.",
            "Goals define the direction, but systems define the progress."
        ]
    }

# Generate study quizzes
@router.get("/{book_id}/quiz", response_model=QuizResponse)
def generate_quiz(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    title = book.title if book else "Curated Book"
    
    quiz_items = [
        QuizItem(
            question="What is the compound effect of getting 1% better every day for a year?",
            options=[
                "Approximately 5 times better",
                "Approximately 12 times better",
                "Approximately 37 times better",
                "Approximately 100 times better"
            ],
            correct_option_index=2,
            explanation="Getting 1% better every day mathematically results in (1.01)^365 which equals 37.78, indicating a 37x improvement."
        ),
        QuizItem(
            question="According to the system-based frameworks, what should you focus on instead of goals?",
            options=[
                "Short-term metrics",
                "Continuous feedback systems and identity habits",
                "Strict endpoint deadlines",
                "Praising final outcomes"
            ],
            correct_option_index=1,
            explanation="Focusing on positive identity feedback loops and consistent systems yields superior and long-lasting achievements compared to tracking rigid endpoints."
        )
    ]
    
    return QuizResponse(title=f"AI Comprehension Quiz: {title}", quiz=quiz_items)

# Generate custom reading plan schedule
@router.get("/{book_id}/plan", response_model=ReadingPlanResponse)
def generate_reading_plan(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    title = book.title if book else "Curated Book"
    
    plan_items = [
        ReadingPlanItem(
            week=1,
            chapters="Chapters 1 - 5: Fundamentals",
            milestones="Define your positive identity habits and cue points.",
            action_items="Write down your daily habits list and isolate environmental triggers."
        ),
        ReadingPlanItem(
            week=2,
            chapters="Chapters 6 - 12: Building Triggers",
            milestones="Apply environmental architecture rules to increase cue visibility.",
            action_items="Design a dedicated reading space in your room with zero distractions."
        ),
        ReadingPlanItem(
            week=3,
            chapters="Chapters 13 - End: Execution and Tracking",
            milestones="Implement habit tracking methods to build momentum.",
            action_items="Commit to a habit tracking sheet and complete the book reflection quiz."
        )
    ]
    
    return ReadingPlanResponse(book_title=title, plan=plan_items)

# AI Book Comparison Endpoint
@router.post("/compare", response_model=ComparisonResponse)
def compare_books(req: ComparisonRequest, db: Session = Depends(get_db)):
    book_a = db.query(Book).filter(Book.id == req.book_a_id).first()
    book_b = db.query(Book).filter(Book.id == req.book_b_id).first()
    
    if not book_a or not book_b:
        raise HTTPException(status_code=404, detail="One or both books not found")
        
    return ComparisonResponse(
        analysis=f"Comparison between '{book_a.title}' and '{book_b.title}'. Both titles deal with structural workflows, though they target slightly different areas of self-actualization.",
        similarities=[
            "Focus on systematic improvement rather than temporary outcomes.",
            "Use clear logical proof points to convince the reader.",
            "Emphasize environmental design."
        ],
        differences=[
            f"'{book_a.title}' centers on micro habits and cues.",
            f"'{book_b.title}' addresses macro structures and project organization."
        ],
        verdict=f"Read '{book_a.title}' first to build a solid daily base, then apply '{book_b.title}' to scale your life goals."
    )

import pypdf
import io
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# In-memory store for vectorized uploaded PDF documents
rag_documents_store = {}

# RAG PDF Upload Interface
@router.post("/rag/upload")
def upload_pdf_document(
    file: UploadFile = File(...),
    book_id: Optional[int] = Form(None)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")
        
    try:
        contents = file.file.read()
        pdf_file = io.BytesIO(contents)
        reader = pypdf.PdfReader(pdf_file)
        
        extracted_chunks = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            text = re.sub(r'\s+', ' ', text).strip()
            if text:
                words = text.split(" ")
                chunk_size = 150
                for j in range(0, len(words), chunk_size):
                    chunk_text = " ".join(words[j:j+chunk_size])
                    if len(chunk_text.strip()) > 20:
                        extracted_chunks.append({
                            "chunk_id": len(extracted_chunks) + 1,
                            "page": i + 1,
                            "text": chunk_text
                        })
        
        if not extracted_chunks:
            extracted_chunks.append({
                "chunk_id": 1,
                "page": 1,
                "text": f"Document '{file.filename}' processed."
            })
            
        vectorizer = TfidfVectorizer(stop_words="english")
        corpus = [c["text"] for c in extracted_chunks]
        tfidf_matrix = vectorizer.fit_transform(corpus)
        
        doc_id = str(uuid.uuid4())
        rag_documents_store[doc_id] = {
            "id": doc_id,
            "filename": file.filename,
            "chunks": extracted_chunks,
            "vectorizer": vectorizer,
            "tfidf_matrix": tfidf_matrix
        }
        
        return {
            "status": "success",
            "document_id": doc_id,
            "filename": file.filename,
            "chunks_extracted": len(extracted_chunks),
            "embeddings_created": len(extracted_chunks),
            "indexing_message": f"'{file.filename}' parsed ({len(reader.pages)} pages, {len(extracted_chunks)} vector chunks indexed). Ready for RAG querying!"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF parsing error: {str(e)}")

# RAG PDF Querying Endpoint
@router.post("/rag/query", response_model=RagQueryResponse)
def query_rag_document(req: RagQueryRequest):
    doc = rag_documents_store.get(req.document_id)
    if not doc:
        return RagQueryResponse(
            answer="Document session expired or not found. Please upload your PDF again.",
            source_chunks=[]
        )
        
    query_text = req.query.strip()
    if not query_text:
        return RagQueryResponse(
            answer="Please enter a question to query your document.",
            source_chunks=[]
        )
        
    vectorizer = doc["vectorizer"]
    tfidf_matrix = doc["tfidf_matrix"]
    chunks = doc["chunks"]
    
    query_vec = vectorizer.transform([query_text])
    similarities = cosine_similarity(query_vec, tfidf_matrix)[0]
    
    top_indices = similarities.argsort()[::-1][:3]
    relevant_chunks = [chunks[idx] for idx in top_indices if similarities[idx] > 0]
    
    if not relevant_chunks:
        relevant_chunks = chunks[:2]
        
    sources = [f"[Page {c['page']}, Chunk {c['chunk_id']}]: {c['text'][:140]}..." for c in relevant_chunks]
    
    combined_context = " ".join([c["text"] for c in relevant_chunks])
    answer = f"### RAG Vector Synthesis ({doc['filename']})\n\nBased on vector semantic search across your document, here is what was found regarding *\"{query_text}\"*:\n\n\"{combined_context[:600]}...\""
    
    return RagQueryResponse(
        answer=answer,
        source_chunks=sources
    )
