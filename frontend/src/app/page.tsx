"use client";

import React, { useState, useEffect } from "react";

import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { StatCards } from "@/components/dashboard/StatCards";
import { BookCard } from "@/components/books/BookCard";
import { AIAssistant } from "@/components/chat/AIAssistant";
// Types
interface ExplainabilityInfo {
  why: string;
  genre_similarity: number;
  reader_overlap: number;
  semantic_similarity: number;
  popularity_score: number;
  personalization_score: number;
  confidence_score: number;
}

interface Book {
  id: number;
  title: string;
  author: string;
  publisher?: string;
  isbn?: string;
  image_url_s?: string;
  image_url_m?: string;
  image_url_l?: string;
  description?: string;
  rating_avg: number;
  rating_count: number;
  genres?: string;
  explainability?: ExplainabilityInfo;
}

interface User {
  id: number;
  email: string;
  full_name?: string;
  role: string;
  reading_streak: number;
  xp_points: number;
  badges: string;
  favorite_genres: string;
  reading_challenge_count: number;
}

interface ChatMessage {
  sender: "user" | "ai";
  text: string;
}

interface QuizItem {
  question: string;
  options: string[];
  correct_option_index: number;
  explanation: string;
}

interface ReadingPlanItem {
  week: number;
  chapters: string;
  milestones: string;
  action_items: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://books-fc3d.onrender.com";

export default function NextGenDashboard() {
  const [activeTab, setActiveTab] = useState<string>("dashboard");
  const [theme, setTheme] = useState<"dark" | "light">("light");
  const [authToken, setAuthToken] = useState<string>("");
  const [user, setUser] = useState<User | null>(null);
  
  // Auth state
  const [authEmail, setAuthEmail] = useState<string>("");
  const [authPassword, setAuthPassword] = useState<string>("");
  const [authName, setAuthName] = useState<string>("");
  const [authGenres, setAuthGenres] = useState<string>("Fiction;Sci-Fi");
  const [isRegistering, setIsRegistering] = useState<boolean>(false);

  // App States
  const [books, setBooks] = useState<Book[]>([]);
  const [recommendations, setRecommendations] = useState<Book[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [genreFilter, setGenreFilter] = useState<string>("");
  const [sessionContext, setSessionContext] = useState<string[]>([]);
  
  // Book title recommendation search states
  const [recSearchInput, setRecSearchInput] = useState<string>("");
  const [recSuggestions, setRecSuggestions] = useState<{ title: string; author: string }[]>([]);
  const [showSuggestions, setShowSuggestions] = useState<boolean>(false);
  const [isRecLoading, setIsRecLoading] = useState<boolean>(false);

  const handleFetchRecsForBook = (bookTitle: string) => {
    const updatedContext = [bookTitle];
    setSessionContext(updatedContext);
    setRecSearchInput(bookTitle);
    setShowSuggestions(false);
    setActiveTab("recommendations");
    fetchRecommendations(updatedContext);
  };

  const handleSearchInputChange = async (value: string) => {
    setRecSearchInput(value);
    if (value.trim().length >= 2) {
      try {
        const res = await fetch(`${API_BASE}/api/search/suggest?q=${encodeURIComponent(value)}`);
        if (res.ok) {
          const data = await res.json();
          setRecSuggestions(data);
          setShowSuggestions(true);
        }
      } catch (err) {
        console.error(err);
      }
    } else {
      setRecSuggestions([]);
      setShowSuggestions(false);
    }
  };

  // Quiz & Coach states
  const [selectedBook, setSelectedBook] = useState<Book | null>(null);
  const [detailBook, setDetailBook] = useState<Book | null>(null);
  const [isAddingToContext, setIsAddingToContext] = useState<boolean>(false);
  const [quizList, setQuizList] = useState<QuizItem[]>([]);
  const [readingPlan, setReadingPlan] = useState<ReadingPlanItem[]>([]);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState<string>("");
  const [ragDoc, setRagDoc] = useState<{ id: string; filename: string } | null>(null);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [ragQueryText, setRagQueryText] = useState<string>("");
  const [ragAnswer, setRagAnswer] = useState<string>("");
  const [ragSources, setRagSources] = useState<string[]>([]);
  const [isUploadingPdf, setIsUploadingPdf] = useState<boolean>(false);
  const [isQueryingRag, setIsQueryingRag] = useState<boolean>(false);
  
  // Notification states
  const [notificationCount, setNotificationCount] = useState<number>(0);
  const [showNotificationsMenu, setShowNotificationsMenu] = useState<boolean>(false);
  
  // Social states
  const [leaderboard, setLeaderboard] = useState<User[]>([]);

  // External Redirect Buy URL Helpers
  const getAmazonBuyUrl = (title: string, author: string) => {
    return `https://www.amazon.in/s?k=${encodeURIComponent(title + " " + author + " book")}`;
  };

  const getFlipkartBuyUrl = (title: string, author: string) => {
    return `https://www.flipkart.com/search?q=${encodeURIComponent(title + " " + author + " book")}`;
  };

  const getGoogleBooksUrl = (title: string, author: string) => {
    return `https://www.google.com/search?tbm=bks&q=${encodeURIComponent(title + " " + author)}`;
  };

  // Helper for consistent number formatting across SSR and Client (prevents hydration mismatch)
  const formatNum = (num: number) => {
    if (num === undefined || num === null) return "0";
    return num.toLocaleString("en-US");
  };

  // Platform Stats & Analytics (Defaults to 0 if no DB data)
  const [platformStats, setPlatformStats] = useState<{
    total_users: number;
    total_books: number;
    total_ratings: number;
    recommendation_ctr: number;
    dau: number;
    mau: number;
  }>({
    total_users: 0,
    total_books: 0,
    total_ratings: 0,
    recommendation_ctr: 0,
    dau: 0,
    mau: 0
  });
  const [ctrByModel, setCtrByModel] = useState<{ label: string; value: number }[]>([]);

  const fetchAnalytics = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/analytics/dashboard`);
      if (res.ok) {
        const data = await res.json();
        if (data && data.stats) {
          setPlatformStats(data.stats);
        }
        if (data && data.ctr_by_model) {
          setCtrByModel(data.ctr_by_model);
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Seed default items if API isn't responding
  useEffect(() => {
    // Attempt local storage fetch
    const storedToken = localStorage.getItem("token");
    if (storedToken) {
      setAuthToken(storedToken);
      fetchProfile(storedToken);
    } else {
      // Mock local User by default to match screenshot view
      setUser({
        id: 1,
        email: "admin@nextgenreads.ai",
        full_name: "Admin User",
        role: "admin",
        reading_streak: 5,
        xp_points: 12450,
        badges: "pioneer, top_recommender",
        favorite_genres: "Fiction, Tech, Sci-Fi",
        reading_challenge_count: 24
      });
    }
    fetchBooks();
    fetchPopularBooks();
    fetchLeaderboard();
    fetchAnalytics();
  }, []);

  const fetchProfile = async (token: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const userData = await res.json();
        setUser(userData);
      }
    } catch (e) {
      setUser({
        id: 1,
        email: "admin@nextgenreads.ai",
        full_name: "Admin User",
        role: "admin",
        reading_streak: 5,
        xp_points: 12450,
        badges: "pioneer, top_recommender",
        favorite_genres: "Fiction, Tech, Sci-Fi",
        reading_challenge_count: 24
      });
    }
  };

  const [popularBooks, setPopularBooks] = useState<Book[]>([]);

  const fetchPopularBooks = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/books/popular`);
      if (res.ok) {
        const data = await res.json();
        setPopularBooks(data);
      }
    } catch (e) {
      console.error("Error fetching popular books:", e);
    }
  };

  const fetchBooks = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/books/?limit=100`);
      if (res.ok) {
        const data = await res.json();
        setBooks(data);
      } else {
        throw new Error();
      }
    } catch (e) {
      // Seed books fallback
      setBooks([
        { id: 101, title: "Harry Potter and the Prisoner of Azkaban", author: "J. K. Rowling", rating_avg: 4.8, rating_count: 428, genres: "Fiction" },
        { id: 102, title: "Harry Potter and the Goblet of Fire", author: "J. K. Rowling", rating_avg: 4.9, rating_count: 387, genres: "Fiction" },
        { id: 103, title: "Atomic Habits", author: "James Clear", rating_avg: 4.8, rating_count: 140, genres: "Self-Help" },
        { id: 104, title: "Deep Work", author: "Cal Newport", rating_avg: 4.6, rating_count: 98, genres: "Productivity" },
        { id: 105, title: "Dune", author: "Frank Herbert", rating_avg: 4.7, rating_count: 310, genres: "Sci-Fi" }
      ]);
    }
  };

  const fetchRecommendations = async (overrideContext?: string[]) => {
    setIsRecLoading(true);
    try {
      const contextStr = (overrideContext || sessionContext).join(",");
      const url = `${API_BASE}/api/recommendations/?limit=6&session_context=${encodeURIComponent(contextStr)}`;
      const headers: Record<string, string> = {};
      if (authToken) {
        headers["Authorization"] = `Bearer ${authToken}`;
      }
      const res = await fetch(url, { headers });
      if (res.ok) {
        const data = await res.json();
        setRecommendations(data);
      } else {
        throw new Error();
      }
    } catch (e) {
      setRecommendations([
        {
          id: 101,
          title: "Atomic Habits",
          author: "James Clear",
          rating_avg: 4.8,
          rating_count: 140,
          genres: "Self-Help",
          explainability: {
            why: "Recommended because it is trending globally with high reader ratings.",
            genre_similarity: 0.85,
            reader_overlap: 0.72,
            semantic_similarity: 0.9,
            popularity_score: 0.95,
            personalization_score: 0.6,
            confidence_score: 0.88
          }
        },
        {
          id: 102,
          title: "Deep Work",
          author: "Cal Newport",
          rating_avg: 4.6,
          rating_count: 98,
          genres: "Productivity",
          explainability: {
            why: "Recommended based on your interest in structural focus frameworks.",
            genre_similarity: 0.9,
            reader_overlap: 0.65,
            semantic_similarity: 0.85,
            popularity_score: 0.8,
            personalization_score: 0.75,
            confidence_score: 0.82
          }
        }
      ]);
    } finally {
      setIsRecLoading(false);
    }
  };

  const fetchLeaderboard = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/auth/leaderboard`);
      if (res.ok) {
        const data = await res.json();
        setLeaderboard(data);
      }
    } catch (e) {
      setLeaderboard([
        { id: 1, email: "bookworm32@reads.ai", full_name: "BookWorm_32", role: "user", reading_streak: 12, xp_points: 12450, badges: "gold_member", favorite_genres: "Sci-Fi", reading_challenge_count: 20 },
        { id: 2, email: "readmore99@reads.ai", full_name: "ReadMore99", role: "user", reading_streak: 8, xp_points: 9870, badges: "silver_member", favorite_genres: "Fiction", reading_challenge_count: 15 },
        { id: 3, email: "aiexplorer@reads.ai", full_name: "AI_Explorer", role: "user", reading_streak: 3, xp_points: 8420, badges: "bronze_member", favorite_genres: "Self-Help", reading_challenge_count: 5 },
        { id: 4, email: "novelninja@reads.ai", full_name: "NovelNinja", role: "user", reading_streak: 4, xp_points: 7150, badges: "bronze_member", favorite_genres: "Fiction", reading_challenge_count: 6 }
      ]);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const formData = new URLSearchParams();
      formData.append("username", authEmail);
      formData.append("password", authPassword);

      const res = await fetch(`${API_BASE}/api/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem("token", data.access_token);
        setAuthToken(data.access_token);
        setUser(data.user);
        setActiveTab("dashboard");
      } else {
        alert("Incorrect login details");
      }
    } catch (e) {
      alert("Backend offline. Simulating mock user login.");
      setUser({
        id: 1,
        email: authEmail || "admin@nextgenreads.ai",
        full_name: authName || "Admin User",
        role: "admin",
        reading_streak: 5,
        xp_points: 12450,
        badges: "pioneer, top_recommender",
        favorite_genres: "Fiction, Tech, Sci-Fi",
        reading_challenge_count: 24
      });
      setActiveTab("dashboard");
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: authEmail,
          password: authPassword,
          full_name: authName,
          favorite_genres: authGenres
        })
      });
      if (res.ok) {
        setIsRegistering(false);
        alert("Registration successful! Please login.");
      }
    } catch (e) {
      alert("Registration request mocked.");
      setIsRegistering(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    setAuthToken("");
    setUser(null);
  };

  const handleBookClick = (title: string) => {
    const updated = [...sessionContext, title].slice(-5);
    setSessionContext(updated);
    fetchRecommendations(updated);
  };

  const handleOpenDetails = async (book: Book) => {
    setDetailBook(book);
    try {
      const res = await fetch(`${API_BASE}/api/books/${book.id}`);
      if (res.ok) {
        const fullBook = await res.json();
        setDetailBook({
          ...fullBook,
          explainability: book.explainability || fullBook.explainability
        });
      }
    } catch (e) {
      console.error("Error fetching book details:", e);
    }
  };

  const handleAddToContextInModal = (title: string) => {
    if (sessionContext.includes(title)) return;
    const updated = [...sessionContext, title].slice(-5);
    setSessionContext(updated);
    fetchRecommendations(updated);
  };

  // Chat/RAG coach workflow
  const loadQuiz = async (bookId: number) => {
    try {
      const res = await fetch(`${API_BASE}/api/chat/${bookId}/quiz`);
      if (res.ok) {
        const data = await res.json();
        setQuizList(data.quiz);
      }
    } catch (e) {
      setQuizList([
        {
          question: "What is the compound effect of getting 1% better every day for a year?",
          options: ["5 times", "12 times", "37 times", "100 times"],
          correct_option_index: 2,
          explanation: "Getting 1% better every day yields 1.01^365 = 37.78x improvements."
        }
      ]);
    }
  };

  const loadPlan = async (bookId: number) => {
    try {
      const res = await fetch(`${API_BASE}/api/chat/${bookId}/plan`);
      if (res.ok) {
        const data = await res.json();
        setReadingPlan(data.plan);
      }
    } catch (e) {
      setReadingPlan([
        { week: 1, chapters: "1-5", milestones: "Set habits", action_items: "Create list" }
      ]);
    }
  };

  const handleCoachChat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    const userText = chatInput;
    const history: ChatMessage[] = [...chatMessages, { sender: "user" as const, text: userText }];
    setChatMessages(history);
    setChatInput("");

    // If a RAG document is active, query document context
    if (ragDoc) {
      try {
        const res = await fetch(`${API_BASE}/api/chat/rag/query`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            document_id: ragDoc.id,
            query: userText
          })
        });
        if (res.ok) {
          const data = await res.json();
          setChatMessages([...history, { sender: "ai" as const, text: data.answer }]);
          return;
        }
      } catch (e) {
        console.error(e);
      }
    }

    try {
      const res = await fetch(`${API_BASE}/api/chat/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`
        },
        body: JSON.stringify({
          message: userText,
          book_id: selectedBook?.id
        })
      });
      if (res.ok) {
        const data = await res.json();
        setChatMessages([...history, { sender: "ai" as const, text: data.response }]);
      }
    } catch (e) {
      setChatMessages([...history, { sender: "ai" as const, text: "AI Coach: Ask questions about your catalog books or uploaded PDF documents." }]);
    }
  };

  const handlePdfUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pdfFile) {
      alert("Please select a PDF file first.");
      return;
    }
    setIsUploadingPdf(true);
    const formData = new FormData();
    formData.append("file", pdfFile);

    try {
      const res = await fetch(`${API_BASE}/api/chat/rag/upload`, {
        method: "POST",
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        setRagDoc({ id: data.document_id, filename: data.filename });
        setRagAnswer("");
        setRagSources([]);
        alert(data.indexing_message || "PDF parsed and vector indexed!");
      } else {
        const err = await res.json();
        alert(`Error uploading PDF: ${err.detail || "Failed to parse PDF"}`);
      }
    } catch (e) {
      alert("Backend connection error. Please ensure server is running.");
    } finally {
      setIsUploadingPdf(false);
    }
  };

  const handleRagQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ragDoc || !ragQueryText.trim()) return;
    setIsQueryingRag(true);
    try {
      const res = await fetch(`${API_BASE}/api/chat/rag/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          document_id: ragDoc.id,
          query: ragQueryText
        })
      });
      if (res.ok) {
        const data = await res.json();
        setRagAnswer(data.answer);
        setRagSources(data.source_chunks || []);
      }
    } catch (e) {
      console.error("RAG query error:", e);
    } finally {
      setIsQueryingRag(false);
    }
  };

  // UI Theme Styling mapping helpers
  const isDark = theme === "dark";


  return (
    <div className="app-container" data-theme={theme}>
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        isDark={isDark} 
        setTheme={setTheme} 
        user={user} 
        handleLogout={handleLogout} 
        fetchRecommendations={() => fetchRecommendations()} 
      />
      <main className="main-content">
        <Header 
          searchQuery={searchQuery} 
          setSearchQuery={setSearchQuery} 
          activeTab={activeTab} 
          setActiveTab={setActiveTab} 
          notificationCount={notificationCount} 
          setNotificationCount={setNotificationCount} 
          user={user} 
        />
        
        <div style={{ marginTop: "2rem" }}>
          {activeTab === "dashboard" && (
            <div className="animate-fade-in flex-col gap-xl">
              <div className="glass-panel flex-row items-center justify-between" style={{ padding: "3rem", background: "linear-gradient(135deg, var(--bg-surface) 0%, var(--bg-elevated) 100%)" }}>
                <div style={{ maxWidth: "600px" }}>
                  <h1 className="text-gradient">Discover Books Powered by Hybrid AI</h1>
                  <p className="text-muted" style={{ marginBottom: "2rem", fontSize: "1.1rem" }}>
                    Experience a state-of-the-art recommendation workflow with Collaborative Filtering, Content Analysis, Semantic Search, and Real-time Reranking.
                  </p>
                  <form onSubmit={(e) => { e.preventDefault(); if (recSearchInput.trim()) handleFetchRecsForBook(recSearchInput.trim()); }} className="flex-row gap-sm">
                    <input 
                      type="text" 
                      placeholder="Type a book title (e.g. Harry Potter)..." 
                      value={recSearchInput}
                      onChange={(e) => handleSearchInputChange(e.target.value)}
                      className="input-field"
                      style={{ flex: 1, padding: "1rem" }}
                    />
                    <button type="submit" className="btn btn-primary" style={{ padding: "1rem 2rem" }}>Recommend</button>
                  </form>
                </div>
              </div>
              <StatCards platformStats={platformStats} formatNum={formatNum} />
            </div>
          )}

          {activeTab === "recommendations" && (
            <div className="animate-fade-in">
              <h2 className="text-gradient">AI Recommendations</h2>
              {isRecLoading ? (
                <div style={{ padding: "3rem", textAlign: "center", color: "var(--primary)" }}>Loading personalized recommendations...</div>
              ) : (
                <div className="grid-cards">
                  {recommendations.map(book => (
                    <BookCard key={book.id} book={book} onClick={handleOpenDetails} />
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === "catalog" && (
            <div className="animate-fade-in">
              <h2 className="text-gradient">Book Catalog</h2>
              <div className="grid-cards">
                {books.map(book => (
                  <BookCard key={book.id} book={book} onClick={handleOpenDetails} />
                ))}
              </div>
            </div>
          )}

          {activeTab === "coach" && (
            <div className="animate-fade-in" style={{ height: "calc(100vh - 200px)" }}>
              <AIAssistant 
                chatMessages={chatMessages}
                chatInput={chatInput}
                setChatInput={setChatInput}
                handleCoachChat={handleCoachChat}
                ragDoc={ragDoc}
                pdfFile={pdfFile}
                setPdfFile={setPdfFile}
                handlePdfUpload={handlePdfUpload}
                isUploadingPdf={isUploadingPdf}
              />
            </div>
          )}

          {activeTab === "auth" && !user && (
            <div className="animate-fade-in flex-row justify-center items-center" style={{ minHeight: "50vh" }}>
              <div className="glass-panel" style={{ width: "100%", maxWidth: "400px", padding: "2rem" }}>
                <h2 className="text-gradient text-center">Welcome Back</h2>
                <form onSubmit={handleLogin} className="flex-col gap-md mt-lg">
                  <div className="input-group">
                    <label className="input-label">Email</label>
                    <input type="email" value={authEmail} onChange={e => setAuthEmail(e.target.value)} className="input-field" required />
                  </div>
                  <div className="input-group">
                    <label className="input-label">Password</label>
                    <input type="password" value={authPassword} onChange={e => setAuthPassword(e.target.value)} className="input-field" required />
                  </div>
                  <button type="submit" className="btn btn-primary" style={{ width: "100%", marginTop: "1rem" }}>Sign In</button>
                </form>
              </div>
            </div>
          )}

          {/* Book Details Modal */}
          {detailBook && (
            <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", backdropFilter: "blur(4px)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100 }}>
              <div className="glass-panel" style={{ width: "90%", maxWidth: "800px", maxHeight: "90vh", overflowY: "auto", position: "relative", padding: "2rem" }}>
                <button onClick={() => setDetailBook(null)} className="btn-ghost" style={{ position: "absolute", top: "1rem", right: "1rem", padding: "0.5rem" }}>✕</button>
                <div className="flex-row gap-xl">
                  <img src={detailBook.image_url_m} style={{ width: "200px", borderRadius: "var(--radius-lg)" }} />
                  <div>
                    <h2 style={{ marginBottom: "0.5rem" }}>{detailBook.title}</h2>
                    <h4 className="text-muted">{detailBook.author}</h4>
                    <p style={{ marginTop: "1rem", lineHeight: 1.6 }}>{detailBook.description || "No description available."}</p>
                    
                    {detailBook.explainability && (
                      <div className="glass-panel" style={{ marginTop: "2rem", padding: "1.5rem", background: "rgba(139, 92, 246, 0.05)", borderColor: "rgba(139, 92, 246, 0.2)" }}>
                        <h4 style={{ color: "var(--primary)", marginBottom: "1rem" }}>Why this was recommended</h4>
                        <p style={{ fontSize: "0.9rem", fontStyle: "italic" }}>"{detailBook.explainability.why}"</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
