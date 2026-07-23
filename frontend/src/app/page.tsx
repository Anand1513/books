"use client";

import React, { useState, useEffect } from "react";

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
        const res = await fetch(`http://127.0.0.1:8000/api/search/suggest?q=${encodeURIComponent(value)}`);
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
      const res = await fetch("http://127.0.0.1:8000/api/analytics/dashboard");
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
      const res = await fetch("http://127.0.0.1:8000/api/auth/me", {
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
      const res = await fetch("http://127.0.0.1:8000/api/books/popular");
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
      const res = await fetch("http://127.0.0.1:8000/api/books/?limit=100");
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
    try {
      const contextStr = (overrideContext || sessionContext).join(",");
      const url = `http://127.0.0.1:8000/api/recommendations/?limit=6&session_context=${encodeURIComponent(contextStr)}`;
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
    }
  };

  const fetchLeaderboard = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/auth/leaderboard");
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

      const res = await fetch("http://127.0.0.1:8000/api/auth/token", {
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
      const res = await fetch("http://127.0.0.1:8000/api/auth/register", {
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
      const res = await fetch(`http://127.0.0.1:8000/api/books/${book.id}`);
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
      const res = await fetch(`http://127.0.0.1:8000/api/chat/${bookId}/quiz`);
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
      const res = await fetch(`http://127.0.0.1:8000/api/chat/${bookId}/plan`);
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
        const res = await fetch("http://127.0.0.1:8000/api/chat/rag/query", {
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
      const res = await fetch("http://127.0.0.1:8000/api/chat/", {
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
      const res = await fetch("http://127.0.0.1:8000/api/chat/rag/upload", {
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
      const res = await fetch("http://127.0.0.1:8000/api/chat/rag/query", {
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
    <div className={`min-h-screen flex transition-colors duration-300 font-sans ${isDark ? "bg-[#0b0f19] text-slate-100" : "bg-[#f8fafc] text-slate-800"}`}>
      
      {/* LEFT SIDEBAR */}
      <aside className={`w-68 flex-shrink-0 border-r flex flex-col justify-between p-6 h-screen sticky top-0 transition-colors duration-300 ${isDark ? "bg-[#111827] border-slate-800" : "bg-white border-slate-100"}`}>
        
        <div className="space-y-6">
          {/* Logo Section */}
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-blue-600 flex items-center justify-center font-bold text-white shadow-md shadow-blue-500/20 text-lg">
              📚
            </div>
            <div>
              <h2 className={`text-xs font-extrabold tracking-tight leading-snug ${isDark ? "text-white" : "text-slate-900"}`}>Book Recommendation System</h2>
              <p className="text-[9px] text-slate-400 font-semibold uppercase tracking-widest mt-0.5">AI Recommender Engine</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1.5 pt-4">
            {[
              { id: "dashboard", label: "Dashboard", icon: (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
              )},
              { id: "recommendations", label: "AI Recommendations", icon: (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 21l8.982-11.795H14.18l1.007-6.009H9.18L6 14.18H9.81"/></svg>
              )},
              { id: "catalog", label: "Catalog", icon: (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
              )},
              { id: "coach", label: "AI Reading Coach", icon: (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222M12 20v-8m4 8v-7.5l-4-2.222"/></svg>
              )},
              { id: "admin", label: "Admin Portal", icon: (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
              )}
            ].map((link) => {
              const active = activeTab === link.id;
              return (
                <button
                  key={link.id}
                  onClick={() => {
                    setActiveTab(link.id);
                    if (link.id === "recommendations") fetchRecommendations();
                  }}
                  className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                    active 
                      ? "bg-blue-600 text-white shadow-sm shadow-blue-500/10" 
                      : `${isDark ? "text-slate-400 hover:bg-slate-800/50 hover:text-slate-100" : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"}`
                  }`}
                >
                  {link.icon}
                  {link.label}
                </button>
              );
            })}
          </nav>

          {/* Pipeline Actions */}
          <div className="pt-4 border-t border-slate-200/50 dark:border-slate-800">
            <h4 className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-3 text-left">Pipeline</h4>
            <div className="space-y-1">
              <button 
                onClick={() => { setActiveTab("recommendations"); fetchRecommendations(); }}
                className={`w-full flex items-center gap-3 px-4 py-2 rounded-xl text-xs text-left ${isDark ? "text-slate-300 hover:bg-slate-800" : "text-slate-700 hover:bg-slate-100"}`}
              >
                <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5"/></svg>
                Generate Recs
              </button>
              <button 
                onClick={() => setActiveTab("coach")}
                className={`w-full flex items-center gap-3 px-4 py-2 rounded-xl text-xs text-left ${isDark ? "text-slate-300 hover:bg-slate-800" : "text-slate-700 hover:bg-slate-100"}`}
              >
                <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5h10.5M12 3a9 9 0 100 18 9 9 0 000-18z"/></svg>
                Upload RAG PDF
              </button>
            </div>
          </div>

          {/* Stats Overview */}
          <div className="pt-4 border-t border-slate-200/50 dark:border-slate-800">
            <h4 className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-3 text-left">Stats Overview</h4>
            <div className="grid grid-cols-2 gap-3 text-left">
              <div className={`p-2.5 rounded-xl border ${isDark ? "bg-slate-900/40 border-slate-800" : "bg-slate-50/50 border-slate-200/50"}`}>
                <span className="text-[9px] text-slate-400 block">Books in Catalog</span>
                <span className="text-xs font-bold" suppressHydrationWarning>{formatNum(platformStats.total_books)}</span>
              </div>
              <div className={`p-2.5 rounded-xl border ${isDark ? "bg-slate-900/40 border-slate-800" : "bg-slate-50/50 border-slate-200/50"}`}>
                <span className="text-[9px] text-slate-400 block">Recommendations</span>
                <span className="text-xs font-bold" suppressHydrationWarning>{(platformStats.total_ratings / 1000).toFixed(1)}K</span>
              </div>
              <div className={`p-2.5 rounded-xl border ${isDark ? "bg-slate-900/40 border-slate-800" : "bg-slate-50/50 border-slate-200/50"}`}>
                <span className="text-[9px] text-slate-400 block">Active Users</span>
                <span className="text-xs font-bold" suppressHydrationWarning>{formatNum(platformStats.total_users)}</span>
              </div>
              <div className={`p-2.5 rounded-xl border ${isDark ? "bg-slate-900/40 border-slate-800" : "bg-slate-50/50 border-slate-200/50"}`}>
                <span className="text-[9px] text-slate-400 block">Avg. Rating</span>
                <span className="text-xs font-bold">4.8 / 5</span>
              </div>
            </div>
          </div>
        </div>

        {/* Theme Toggle & User Info at bottom */}
        <div className="space-y-4 pt-4 border-t border-slate-200/50 dark:border-slate-800">
          
          {/* Day/Night Toggle Switch */}
          <div className="flex items-center justify-between px-2">
            <div className="flex items-center gap-2">
              {isDark ? (
                <svg className="w-4 h-4 text-blue-400" fill="currentColor" viewBox="0 0 20 20"><path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"/></svg>
              ) : (
                <svg className="w-4 h-4 text-amber-500" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.46 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 100 2h1z" clipRule="evenodd"/></svg>
              )}
              <span className="text-xs font-medium">Dark Mode</span>
            </div>
            
            <button 
              onClick={() => setTheme(isDark ? "light" : "dark")}
              className={`w-10 h-5 rounded-full p-0.5 transition-colors duration-200 focus:outline-none flex items-center ${isDark ? "bg-blue-600 justify-end" : "bg-slate-200 justify-start"}`}
            >
              <div className="w-4 h-4 rounded-full bg-white shadow-md"></div>
            </button>
          </div>

          {/* User Profile Card */}
          {user ? (
            <div className={`p-2.5 rounded-2xl flex items-center justify-between transition-colors duration-200 ${isDark ? "bg-slate-900/60 hover:bg-slate-800/80" : "bg-slate-550/40 hover:bg-slate-100"}`}>
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center font-bold text-white text-xs flex-shrink-0 animate-[pulse_5s_infinite]">
                  {user.full_name ? user.full_name.charAt(0) : "A"}
                </div>
                <div className="text-left min-w-0">
                  <h4 className="text-xs font-semibold truncate leading-tight">{user.full_name || "Admin User"}</h4>
                  <p className="text-[9px] text-slate-400 truncate mt-0.5">{user.email || "admin@nextgenreads.ai"}</p>
                </div>
              </div>
              <button 
                onClick={handleLogout}
                className="text-[10px] font-bold text-rose-500 hover:text-rose-600 p-1 flex-shrink-0"
                title="Logout"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
              </button>
            </div>
          ) : (
            <button 
              onClick={() => setActiveTab("auth")}
              className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs transition-all shadow-md shadow-blue-500/10"
            >
              Sign In Account
            </button>
          )}
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="flex-1 min-w-0 flex flex-col h-screen overflow-y-auto">
        
        {/* TOP HEADER */}
        <header className={`sticky top-0 z-35 border-b px-8 py-4 flex items-center justify-between transition-colors duration-300 ${isDark ? "bg-[#0b0f19]/80 border-slate-800" : "bg-[#f8fafc]/80 border-slate-200/50"} backdrop-blur-md`}>
          {/* Search Bar */}
          <div className="w-full max-w-lg relative">
            <span className="absolute inset-y-0 left-3 flex items-center pl-1 pointer-events-none text-slate-400">
              <svg className="w-4.5 h-4.5" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
            </span>
            <input 
              type="text" 
              placeholder="Search books, authors, genres..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onClick={() => { if (activeTab !== "catalog" && activeTab !== "dashboard") setActiveTab("catalog"); }}
              className={`w-full pl-10 pr-4 py-2.5 rounded-xl border text-sm transition-all focus:outline-none focus:ring-2 focus:ring-blue-500/20 ${
                isDark 
                  ? "bg-slate-900 border-slate-800 text-slate-200 focus:border-blue-500 placeholder-slate-500" 
                  : "bg-white border-slate-200/60 text-slate-800 focus:border-blue-400 placeholder-slate-400"
              }`}
            />
          </div>

          {/* Action Area */}
          <div className="flex items-center gap-4">
            {/* Notification Bell */}
            <div className="relative">
              <button 
                onClick={() => {
                  setShowNotificationsMenu(!showNotificationsMenu);
                  if (notificationCount > 0) setNotificationCount(0);
                }}
                className={`p-2.5 rounded-xl border relative hover:scale-105 transition-all ${isDark ? "bg-slate-900 border-slate-800 text-slate-300" : "bg-white border-slate-200/50 text-slate-600 shadow-sm"}`}
                title="Notifications"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/></svg>
                {notificationCount > 0 && (
                  <span className="absolute -top-1 -right-1 w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center text-[10px] font-bold border border-white">
                    {notificationCount}
                  </span>
                )}
              </button>

              {showNotificationsMenu && (
                <div className={`absolute right-0 top-full mt-2 w-72 p-4 rounded-2xl border shadow-xl z-50 text-left ${isDark ? "bg-slate-900 border-slate-800 text-slate-200" : "bg-white border-slate-200 text-slate-800"}`}>
                  <div className="flex items-center justify-between border-b pb-2 mb-3 dark:border-slate-800">
                    <h4 className="text-xs font-bold uppercase tracking-wider">Notifications</h4>
                    <span className="text-[10px] text-emerald-500 font-semibold">🟢 Systems Operational</span>
                  </div>
                  <div className="text-xs text-slate-400 text-center py-4">
                    🔔 No unread notifications. All recommendation algorithms up to date!
                  </div>
                </div>
              )}
            </div>

            {/* Profile/Auth Button */}
            {user ? (
              <div className="flex items-center gap-2.5">
                <span className={`text-xs font-semibold ${isDark ? "text-slate-300" : "text-slate-700"}`}>
                  Hi, {user.full_name || "Admin"}
                </span>
                <div className="h-9 w-9 rounded-full bg-blue-600 flex items-center justify-center font-bold text-white text-xs shadow-md shadow-blue-500/25">
                  {user.full_name ? user.full_name.charAt(0) : "A"}
                </div>
              </div>
            ) : (
              <button 
                onClick={() => setActiveTab("auth")}
                className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-md shadow-blue-500/10 transition-all"
              >
                Sign In
              </button>
            )}
          </div>
        </header>

        {/* MAIN BODY CONTAINER */}
        <div className="flex-grow p-8 space-y-8">
          
          {/* TAB 1: DASHBOARD */}
          {activeTab === "dashboard" && (
            <div className="space-y-8">
              
              {/* HERO BANNER SECTION */}
              <div className={`relative rounded-3xl border overflow-hidden p-8 md:p-10 flex flex-col md:flex-row items-center justify-between gap-8 transition-colors duration-300 ${
                isDark 
                  ? "bg-gradient-to-r from-slate-900 via-[#10172a] to-slate-900 border-slate-800" 
                  : "bg-white border-slate-200/50 shadow-sm"
              }`}>
                <div className="space-y-4 max-w-xl text-left z-10">
                  <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 px-4 py-1.5 rounded-full text-blue-600 dark:text-blue-450 text-xs font-semibold uppercase tracking-wider">
                    🚀 Enterprise hybrid pipeline
                  </div>
                  <h1 className={`text-3xl md:text-4xl font-extrabold tracking-tight leading-tight ${isDark ? "text-white" : "text-slate-900"}`}>
                    Discover Books Powered by <span className="text-blue-600 dark:text-blue-400">Hybrid AI</span>
                  </h1>
                  <p className={`text-sm leading-relaxed ${isDark ? "text-slate-350 font-light" : "text-slate-500"}`}>
                    Experience a state-of-the-art recommendation workflow with Collaborative Filtering, Content Analysis, Semantic Search, and Real-time Reranking.
                  </p>
                  
                  {/* Search Bar to enter book title and get similar recommendations */}
                  <div className="pt-2 relative z-20">
                    <form 
                      onSubmit={(e) => {
                        e.preventDefault();
                        if (recSearchInput.trim()) {
                          handleFetchRecsForBook(recSearchInput.trim());
                        }
                      }}
                      className="flex items-center gap-2"
                    >
                      <div className="relative flex-1">
                        <input
                          type="text"
                          placeholder="Type a book title (e.g. Harry Potter, 1984, To Kill a Mockingbird)..."
                          value={recSearchInput}
                          onChange={(e) => handleSearchInputChange(e.target.value)}
                          onFocus={() => { if (recSuggestions.length > 0) setShowSuggestions(true); }}
                          className={`w-full px-4 py-3 rounded-xl border text-xs sm:text-sm font-medium transition-all focus:outline-none focus:ring-2 focus:ring-blue-500/30 ${
                            isDark 
                              ? "bg-slate-900/90 border-slate-700 text-white placeholder-slate-400" 
                              : "bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-500"
                          }`}
                        />
                        {/* Suggestions Autocomplete Dropdown */}
                        {showSuggestions && recSuggestions.length > 0 && (
                          <div className={`absolute left-0 right-0 top-full mt-1.5 rounded-2xl border shadow-xl z-50 overflow-hidden max-h-60 overflow-y-auto ${
                            isDark ? "bg-slate-900 border-slate-800 text-slate-200" : "bg-white border-slate-200 text-slate-800"
                          }`}>
                            <div className="p-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100 dark:border-slate-800">
                              Select a book for recommendations:
                            </div>
                            {recSuggestions.map((item, idx) => (
                              <div
                                key={idx}
                                onClick={() => handleFetchRecsForBook(item.title)}
                                className="p-3 hover:bg-blue-600 hover:text-white cursor-pointer transition-colors text-left flex items-center justify-between border-b last:border-b-0 border-slate-100 dark:border-slate-850"
                              >
                                <span className="font-semibold text-xs truncate max-w-[75%]">{item.title}</span>
                                <span className="text-[10px] opacity-75 italic">{item.author}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                      <button
                        type="submit"
                        className="px-5 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-md shadow-blue-500/20 transition-all flex items-center gap-1.5 flex-shrink-0"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                        Recommend
                      </button>
                    </form>
                  </div>

                  <div className="flex gap-3 pt-1">
                    <button 
                      onClick={() => { setActiveTab("recommendations"); fetchRecommendations(); }}
                      className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs rounded-xl transition-all flex items-center gap-2"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 21l8.982-11.795H14.18l1.007-6.009H9.18L6 14.18H9.81"/></svg>
                      Browse All Hybrid Recs
                    </button>
                    <button 
                      onClick={() => setActiveTab("coach")}
                      className={`px-4 py-2.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200/80 font-semibold text-xs rounded-xl transition-all shadow-sm flex items-center gap-2 ${
                        isDark ? "dark:bg-slate-900 dark:border-slate-800 dark:text-slate-200 dark:hover:bg-slate-850" : ""
                      }`}
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5h10.5M12 3a9 9 0 100 18 9 9 0 000-18z"/></svg>
                      Upload RAG PDF
                    </button>
                  </div>
                </div>

                {/* Animated Pipeline Circle widget */}
                <div className="relative w-72 h-72 flex items-center justify-center z-10 flex-shrink-0">
                  {/* Outer Orbit Path */}
                  <div className={`absolute w-52 h-52 rounded-full border border-dashed animate-[spin_40s_linear_infinite] ${isDark ? "border-slate-800" : "border-slate-200"}`}></div>
                  <div className={`absolute w-36 h-36 rounded-full border border-dotted animate-[spin_20s_linear_infinite_reverse] ${isDark ? "border-slate-800" : "border-slate-200"}`}></div>

                  {/* Pulsing Center Icon */}
                  <div className="w-20 h-20 rounded-full bg-blue-100 dark:bg-blue-950 flex items-center justify-center shadow-lg border border-blue-200/50 dark:border-blue-800 z-10 animate-[pulse_3s_ease-in-out_infinite]">
                    <svg className="w-10 h-10 text-blue-600 dark:text-blue-450" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
                  </div>

                  {/* Floating Tags with dynamic positions */}
                  <div className="absolute top-2 w-max px-3 py-1 bg-purple-50 dark:bg-purple-950/80 border border-purple-200/40 dark:border-purple-800 text-[10px] font-semibold text-purple-600 dark:text-purple-400 rounded-lg shadow-sm">
                    Collaborative Filtering
                  </div>
                  <div className="absolute right-0 top-20 w-max px-3 py-1 bg-pink-50 dark:bg-pink-950/80 border border-pink-200/40 dark:border-pink-850 text-[10px] font-semibold text-pink-600 dark:text-pink-400 rounded-lg shadow-sm">
                    Content Analysis
                  </div>
                  <div className="absolute left-0 bottom-20 w-max px-3 py-1 bg-indigo-50 dark:bg-indigo-950/80 border border-indigo-200/40 dark:border-indigo-850 text-[10px] font-semibold text-indigo-600 dark:text-indigo-400 rounded-lg shadow-sm">
                    Semantic Search
                  </div>
                  <div className="absolute bottom-2 w-max px-3 py-1 bg-sky-50 dark:bg-sky-950/80 border border-sky-200/40 dark:border-sky-850 text-[10px] font-semibold text-sky-600 dark:text-sky-400 rounded-lg shadow-sm">
                    Real-time Reranking
                  </div>
                </div>
              </div>

              {/* TELEMETRY STATS ROW */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                
                {/* Stats Card 1: Books in Catalog */}
                <div className={`p-5 rounded-2xl border text-left transition-all hover:shadow-md ${isDark ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200/50 shadow-sm"}`}>
                  <div className="flex items-center justify-between">
                    <div className="h-9 w-9 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253"/></svg>
                    </div>
                    <span className="text-[10px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 rounded-full flex items-center gap-0.5">
                      ▲ 12.5%
                    </span>
                  </div>
                  <div className="mt-3">
                    <span className="text-[11px] text-slate-400 font-medium block">Books in Catalog</span>
                    <span className="text-2xl font-bold tracking-tight mt-0.5 block" suppressHydrationWarning>{formatNum(platformStats.total_books)}</span>
                  </div>
                  
                  {/* Purple Sparkline SVG */}
                  <div className="h-12 w-full mt-4">
                    <svg className="w-full h-full" viewBox="0 0 200 50" preserveAspectRatio="none">
                      <defs>
                        <linearGradient id="purple-spark" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#6366f1" stopOpacity="0.25"/>
                          <stop offset="100%" stopColor="#6366f1" stopOpacity="0"/>
                        </linearGradient>
                      </defs>
                      <path d="M0 45 L 20 40 L 40 43 L 60 25 L 80 35 L 100 20 L 120 30 L 140 10 L 160 25 L 180 5 L 200 15 L 200 50 L 0 50 Z" fill="url(#purple-spark)"></path>
                      <path d="M0 45 L 20 40 L 40 43 L 60 25 L 80 35 L 100 20 L 120 30 L 140 10 L 160 25 L 180 5 L 200 15" fill="none" stroke="#6366f1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"></path>
                    </svg>
                  </div>
                </div>

                {/* Stats Card 2: Recommendations */}
                <div className={`p-5 rounded-2xl border text-left transition-all hover:shadow-md ${isDark ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200/50 shadow-sm"}`}>
                  <div className="flex items-center justify-between">
                    <div className="h-9 w-9 rounded-lg bg-blue-50 dark:bg-blue-950/50 flex items-center justify-center text-blue-600 dark:text-blue-400">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 21l8.982-11.795H14.18l1.007-6.009H9.18L6 14.18H9.81"/></svg>
                    </div>
                    <span className="text-[10px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 rounded-full flex items-center gap-0.5">
                      ▲ 18.7%
                    </span>
                  </div>
                  <div className="mt-3">
                    <span className="text-[11px] text-slate-400 font-medium block">Recommendations</span>
                    <span className="text-2xl font-bold tracking-tight mt-0.5 block" suppressHydrationWarning>{(platformStats.total_ratings / 1000).toFixed(1)}K</span>
                  </div>
                  
                  {/* Blue Sparkline SVG */}
                  <div className="h-12 w-full mt-4">
                    <svg className="w-full h-full" viewBox="0 0 200 50" preserveAspectRatio="none">
                      <defs>
                        <linearGradient id="blue-spark" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.25"/>
                          <stop offset="100%" stopColor="#3b82f6" stopOpacity="0"/>
                        </linearGradient>
                      </defs>
                      <path d="M0 35 L 20 40 L 40 30 L 60 45 L 80 20 L 100 35 L 120 15 L 140 25 L 160 5 L 180 20 L 200 10 L 200 50 L 0 50 Z" fill="url(#blue-spark)"></path>
                      <path d="M0 35 L 20 40 L 40 30 L 60 45 L 80 20 L 100 35 L 120 15 L 140 25 L 160 5 L 180 20 L 200 10" fill="none" stroke="#3b82f6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"></path>
                    </svg>
                  </div>
                </div>

                {/* Stats Card 3: Active Users */}
                <div className={`p-5 rounded-2xl border text-left transition-all hover:shadow-md ${isDark ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200/50 shadow-sm"}`}>
                  <div className="flex items-center justify-between">
                    <div className="h-9 w-9 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20H7v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/></svg>
                    </div>
                    <span className="text-[10px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 rounded-full flex items-center gap-0.5">
                      ▲ 8.3%
                    </span>
                  </div>
                  <div className="mt-3">
                    <span className="text-[11px] text-slate-400 font-medium block">Active Users</span>
                    <span className="text-2xl font-bold tracking-tight mt-0.5 block" suppressHydrationWarning>{formatNum(platformStats.total_users)}</span>
                  </div>
                  
                  {/* Green Sparkline SVG */}
                  <div className="h-12 w-full mt-4">
                    <svg className="w-full h-full" viewBox="0 0 200 50" preserveAspectRatio="none">
                      <defs>
                        <linearGradient id="green-spark" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#10b981" stopOpacity="0.25"/>
                          <stop offset="100%" stopColor="#10b981" stopOpacity="0"/>
                        </linearGradient>
                      </defs>
                      <path d="M0 45 L 20 42 L 40 45 L 60 30 L 80 32 L 100 25 L 120 28 L 140 15 L 160 20 L 180 12 L 200 5 L 200 50 L 0 50 Z" fill="url(#green-spark)"></path>
                      <path d="M0 45 L 20 42 L 40 45 L 60 30 L 80 32 L 100 25 L 120 28 L 140 15 L 160 20 L 180 12 L 200 5" fill="none" stroke="#10b981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"></path>
                    </svg>
                  </div>
                </div>

                {/* Stats Card 4: Avg Rating */}
                <div className={`p-5 rounded-2xl border text-left transition-all hover:shadow-md ${isDark ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200/50 shadow-sm"}`}>
                  <div className="flex items-center justify-between">
                    <div className="h-9 w-9 rounded-lg bg-amber-50 dark:bg-amber-950/50 flex items-center justify-center text-amber-600 dark:text-amber-500">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"/></svg>
                    </div>
                    <span className="text-[10px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 rounded-full flex items-center gap-0.5">
                      ▲ 0.2
                    </span>
                  </div>
                  <div className="mt-3">
                    <span className="text-[11px] text-slate-400 font-medium block">Avg. Rating</span>
                    <span className="text-2xl font-bold tracking-tight mt-0.5 block">4.8 <span className="text-sm font-normal text-slate-400">/ 5</span></span>
                  </div>
                  
                  {/* Yellow Sparkline SVG */}
                  <div className="h-12 w-full mt-4">
                    <svg className="w-full h-full" viewBox="0 0 200 50" preserveAspectRatio="none">
                      <defs>
                        <linearGradient id="yellow-spark" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.25"/>
                          <stop offset="100%" stopColor="#f59e0b" stopOpacity="0"/>
                        </linearGradient>
                      </defs>
                      <path d="M0 40 L 20 42 L 40 38 L 60 40 L 80 25 L 100 28 L 120 30 L 140 20 L 160 22 L 180 18 L 200 15 L 200 50 L 0 50 Z" fill="url(#yellow-spark)"></path>
                      <path d="M0 40 L 20 42 L 40 38 L 60 40 L 80 25 L 100 28 L 120 30 L 140 20 L 160 22 L 180 18 L 200 15" fill="none" stroke="#f59e0b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"></path>
                    </svg>
                  </div>
                </div>

              </div>

              {/* TOP 50 POPULAR HITS CAROUSEL */}
              <div className={`p-6 rounded-3xl border text-left ${isDark ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200/50 shadow-sm"}`}>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className={`text-lg font-bold flex items-center gap-2 ${isDark ? "text-white" : "text-slate-900"}`}>
                      <span>🔥 Top 50 Popular Hits</span>
                      <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">Curated Dataset</span>
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">Top rated books from readers dataset with highest rating density.</p>
                  </div>
                  <button 
                    onClick={() => setActiveTab("catalog")}
                    className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline flex-shrink-0"
                  >
                    View catalog ({popularBooks.length})
                  </button>
                </div>
                
                <div className="flex gap-4 overflow-x-auto pb-4 pt-2 scrollbar-thin">
                  {popularBooks.map((book, idx) => (
                    <div 
                      key={book.id || idx}
                      onClick={() => handleOpenDetails(book)}
                      className={`w-36 flex-shrink-0 border p-3 rounded-2xl space-y-2 cursor-pointer hover:shadow-md transition-all hover:-translate-y-1 ${
                        isDark ? "bg-slate-955 border-slate-850 hover:border-blue-500/50" : "bg-slate-50 border-slate-200/60 hover:border-blue-400 shadow-sm"
                      }`}
                    >
                      <div className={`w-full h-40 rounded-xl overflow-hidden flex items-center justify-center font-bold text-xl ${isDark ? "bg-slate-900" : "bg-white"}`}>
                        {book.image_url_m ? (
                          <img src={book.image_url_m} alt={book.title} className="w-full h-full object-cover" />
                        ) : (
                          "📖"
                        )}
                      </div>
                      <div>
                        <span className="text-[9px] font-bold text-amber-600 dark:text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded">
                          #{idx + 1} Popular
                        </span>
                        <h4 className="font-bold text-xs line-clamp-1 mt-1 hover:text-blue-550 transition-colors">{book.title}</h4>
                        <p className="text-[10px] text-slate-400 truncate">{book.author}</p>
                        <div className="flex items-center justify-between text-[9px] text-slate-400 pt-1 border-t border-slate-100 dark:border-slate-850 mt-1">
                          <span>⭐ {book.rating_avg ? book.rating_avg.toFixed(1) : "4.8"}</span>
                          <span>{book.rating_count} ratings</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* BOTTOM TWO-COLUMN GRID */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                
                {/* Column 1: Trending Catalog List */}
                <div className={`lg:col-span-2 p-6 rounded-3xl border text-left ${isDark ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200/50 shadow-sm"}`}>
                  <div className="flex items-center justify-between mb-6">
                    <h3 className={`text-base font-bold ${isDark ? "text-white" : "text-slate-900"}`}>Trending in Library</h3>
                    <button 
                      onClick={() => setActiveTab("catalog")}
                      className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      View all
                    </button>
                  </div>
                  
                  <div className="space-y-4">
                    {books.slice(0, 2).map((book) => (
                      <div 
                        key={book.id}
                        onClick={() => handleOpenDetails(book)}
                        className={`p-4 rounded-2xl border flex items-center justify-between gap-4 cursor-pointer transition-all hover:-translate-y-0.5 ${
                          isDark 
                            ? "bg-slate-955 border-slate-850 hover:border-slate-700" 
                            : "bg-[#f8fafc] border-slate-100 hover:border-slate-200 hover:shadow-sm"
                        }`}
                      >
                        <div className="flex items-center gap-4 min-w-0">
                          <div className={`w-12 h-16 rounded-xl flex-shrink-0 flex items-center justify-center font-bold text-lg overflow-hidden ${isDark ? "bg-slate-850" : "bg-white border border-slate-100 shadow-sm"}`}>
                            {book.image_url_m ? (
                              <img src={book.image_url_m} alt={book.title} className="w-full h-full object-cover" />
                            ) : (
                              "📖"
                            )}
                          </div>
                          <div className="min-w-0">
                            <h4 className="text-sm font-bold truncate">{book.title}</h4>
                            <p className="text-xs text-slate-400 mt-0.5">{book.author}</p>
                            <div className="flex items-center gap-2 mt-2">
                              <span className="text-amber-400 text-xs">★</span>
                              <span className="text-[11px] font-bold">{typeof book.rating_avg === 'number' ? (book.rating_avg > 5 ? (book.rating_avg / 2).toFixed(1) : book.rating_avg.toFixed(1)) : book.rating_avg}</span>
                              <span className="text-[10px] text-slate-400">({book.rating_count} reviews)</span>
                              <span className="text-[10px] font-bold bg-blue-100 dark:bg-blue-950 text-blue-600 dark:text-blue-400 px-2 py-0.5 rounded-md">
                                {book.genres || "Fiction"}
                              </span>
                            </div>
                          </div>
                        </div>
                        
                        <div className="text-slate-400">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7"/></svg>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Column 2: Leaderboard */}
                <div className={`p-6 rounded-3xl border text-left ${isDark ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200/50 shadow-sm"}`}>
                  <div className="flex items-center justify-between mb-6">
                    <h3 className={`text-base font-bold ${isDark ? "text-white" : "text-slate-900"}`}>Community Leaderboard</h3>
                    <button 
                      onClick={() => alert("Leaderboard profiles detail simulation activated.")}
                      className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      View all
                    </button>
                  </div>

                  <div className="space-y-4.5">
                    {leaderboard.map((u, idx) => {
                      const isTop1 = idx === 0;
                      const isTop2 = idx === 1;
                      const isTop3 = idx === 2;
                      return (
                        <div key={u.id} className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                              isTop1 ? "bg-amber-500 text-white" : isTop2 ? "bg-slate-300 text-slate-700" : isTop3 ? "bg-amber-700 text-white" : "bg-slate-100 dark:bg-slate-800 text-slate-400"
                            }`}>
                              {idx + 1}
                            </span>
                            
                            <div className="h-8.5 w-8.5 rounded-full bg-blue-100 dark:bg-blue-950 flex items-center justify-center font-bold text-blue-600 dark:text-blue-450 text-xs">
                              {u.full_name ? u.full_name.charAt(0) : "U"}
                            </div>
                            
                            <div>
                              <p className={`text-xs font-bold ${isDark ? "text-slate-200" : "text-slate-855"}`}>{u.full_name || u.email}</p>
                              <p className="text-[10px] text-slate-400 mt-0.5">Streak: {u.reading_streak} days</p>
                            </div>
                          </div>

                          <div className="flex items-center gap-1.5">
                            <span className="text-xs font-extrabold text-blue-600 dark:text-blue-450" suppressHydrationWarning>{formatNum(u.xp_points)}</span>
                            <span className="text-[9px] text-slate-400">pts</span>
                            
                            {isTop1 && <span title="Top Active Reader" className="text-xs">🏆</span>}
                            {isTop2 && <span title="Leader" className="text-xs">🥈</span>}
                            {isTop3 && <span title="Rising Star" className="text-xs">🥉</span>}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

              </div>

            </div>
          )}

          {/* TAB 2: AI RECOMMENDATIONS */}
          {activeTab === "recommendations" && (
            <div className="space-y-6 text-left">
              <div>
                <h2 className={`text-2xl font-extrabold ${isDark ? "text-white" : "text-slate-900"}`}>Hybrid AI Recommendations</h2>
                <p className="text-slate-400 text-xs mt-1">Our 6-stage recommendation pipeline custom tailors catalog items based on your chosen book title.</p>
                
                {/* Search box for selecting/typing a book title */}
                <div className="pt-4 max-w-2xl relative z-20">
                  <form 
                    onSubmit={(e) => {
                      e.preventDefault();
                      if (recSearchInput.trim()) {
                        handleFetchRecsForBook(recSearchInput.trim());
                      }
                    }}
                    className="flex items-center gap-2"
                  >
                    <div className="relative flex-1">
                      <input
                        type="text"
                        placeholder="Type a book title (e.g. Harry Potter, 1984, To Kill a Mockingbird)..."
                        value={recSearchInput}
                        onChange={(e) => handleSearchInputChange(e.target.value)}
                        onFocus={() => { if (recSuggestions.length > 0) setShowSuggestions(true); }}
                        className={`w-full px-4 py-3 rounded-xl border text-xs sm:text-sm font-medium transition-all focus:outline-none focus:ring-2 focus:ring-blue-500/30 ${
                          isDark 
                            ? "bg-slate-900/90 border-slate-700 text-white placeholder-slate-400" 
                            : "bg-white border-slate-300 text-slate-900 placeholder-slate-500 shadow-sm"
                        }`}
                      />
                      {showSuggestions && recSuggestions.length > 0 && (
                        <div className={`absolute left-0 right-0 top-full mt-1.5 rounded-2xl border shadow-xl z-50 overflow-hidden max-h-60 overflow-y-auto ${
                          isDark ? "bg-slate-900 border-slate-800 text-slate-200" : "bg-white border-slate-200 text-slate-800"
                        }`}>
                          <div className="p-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100 dark:border-slate-800">
                            Select a book for recommendations:
                          </div>
                          {recSuggestions.map((item, idx) => (
                            <div
                              key={idx}
                              onClick={() => handleFetchRecsForBook(item.title)}
                              className="p-3 hover:bg-blue-600 hover:text-white cursor-pointer transition-colors text-left flex items-center justify-between border-b last:border-b-0 border-slate-100 dark:border-slate-850"
                            >
                              <span className="font-semibold text-xs truncate max-w-[75%]">{item.title}</span>
                              <span className="text-[10px] opacity-75 italic">{item.author}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    <button
                      type="submit"
                      className="px-5 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-md shadow-blue-500/20 transition-all flex items-center gap-1.5 flex-shrink-0"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                      Recommend
                    </button>
                  </form>
                </div>

                {sessionContext.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-4 items-center">
                    <span className="text-xs text-slate-500 uppercase tracking-wide">Active Context:</span>
                    {sessionContext.map((c, i) => (
                      <span key={i} className="bg-blue-500/10 border border-blue-500/25 text-blue-600 dark:text-blue-450 text-xs px-3 py-1 rounded-full flex items-center gap-1 font-medium">
                        📖 {c}
                      </span>
                    ))}
                    <button onClick={() => { setSessionContext([]); fetchRecommendations([]); }} className="text-xs text-rose-500 font-bold hover:underline ml-2">Clear Context</button>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                {recommendations.map((book) => (
                  <div key={book.id} className={`border rounded-3xl p-6 flex flex-col sm:flex-row gap-6 shadow-sm hover:shadow-md transition-all duration-300 ${
                    isDark ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200/50"
                  }`}>
                    <div 
                      onClick={() => handleOpenDetails(book)}
                      className={`w-full sm:w-36 h-48 rounded-2xl flex-shrink-0 flex items-center justify-center font-bold text-2xl overflow-hidden cursor-pointer hover:opacity-90 transition-all ${
                        isDark ? "bg-slate-850 text-slate-650" : "bg-slate-50 text-slate-400"
                      }`}
                    >
                      {book.image_url_m ? (
                        <img src={book.image_url_m} alt={book.title} className="w-full h-full object-cover" />
                      ) : (
                        "📖"
                      )}
                    </div>
                    
                    <div className="flex-grow flex flex-col justify-between space-y-4">
                      <div>
                        <div className="flex items-center justify-between">
                          <span className="bg-blue-500/10 border border-blue-500/20 text-blue-600 dark:text-blue-400 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-md">
                            {book.genres || "Fiction"}
                          </span>
                          {book.explainability && (
                            <span className="text-xs font-bold text-emerald-500">
                              Confidence: {Math.round(book.explainability.confidence_score * 100)}%
                            </span>
                          )}
                        </div>
                        <h3 
                          onClick={() => handleOpenDetails(book)}
                          className="text-xl font-bold pt-2 line-clamp-1 cursor-pointer hover:text-blue-550 transition-colors"
                        >
                          {book.title}
                        </h3>
                        <p className="text-xs text-slate-450">{book.author}</p>
                        
                        {book.explainability && (
                          <div className={`p-3.5 rounded-xl mt-3 space-y-2 border ${isDark ? "bg-slate-950 border-slate-850" : "bg-slate-50 border-slate-100"}`}>
                            <p className="text-[11px] leading-relaxed font-light">
                              <strong>Why Recommended:</strong> {book.explainability.why}
                            </p>
                            
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-[9px] text-slate-450">
                              <div>
                                <div className="w-full bg-slate-200 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden mb-1">
                                  <div className="bg-blue-500 h-full" style={{ width: `${book.explainability.genre_similarity * 100}%` }}></div>
                                </div>
                                Genre Match: {Math.round(book.explainability.genre_similarity * 100)}%
                              </div>
                              <div>
                                <div className="w-full bg-slate-200 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden mb-1">
                                  <div className="bg-purple-500 h-full" style={{ width: `${book.explainability.reader_overlap * 100}%` }}></div>
                                </div>
                                Reader Overlap: {Math.round(book.explainability.reader_overlap * 100)}%
                              </div>
                              <div>
                                <div className="w-full bg-slate-200 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden mb-1">
                                  <div className="bg-emerald-500 h-full" style={{ width: `${book.explainability.semantic_similarity * 100}%` }}></div>
                                </div>
                                Semantic Sim: {Math.round(book.explainability.semantic_similarity * 100)}%
                              </div>
                              <div>
                                <div className="w-full bg-slate-200 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden mb-1">
                                  <div className="bg-amber-500 h-full" style={{ width: `${book.explainability.popularity_score * 100}%` }}></div>
                                </div>
                                Popularity: {Math.round(book.explainability.popularity_score * 100)}%
                              </div>
                            </div>
                          </div>
                        )}
                      </div>

                      <div className={`flex flex-wrap gap-2 pt-3 border-t ${isDark ? "border-slate-800" : "border-slate-100"}`}>
                        <button onClick={() => { setSelectedBook(book); setActiveTab("coach"); loadQuiz(book.id); loadPlan(book.id); }} className={`px-3 py-2 rounded-xl text-xs font-semibold flex-1 ${isDark ? "bg-slate-800 hover:bg-slate-750 text-slate-200" : "bg-slate-100 hover:bg-slate-200 text-slate-700"}`}>
                          Study Coach
                        </button>
                        <button onClick={() => handleBookClick(book.title)} className="px-3 py-2 rounded-xl bg-blue-500/10 hover:bg-blue-500/20 text-blue-600 dark:text-blue-400 text-xs font-semibold">
                          Add context
                        </button>
                        <a 
                          href={getAmazonBuyUrl(book.title, book.author)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-3 py-2 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-700 dark:text-amber-400 text-xs font-bold flex items-center gap-1 border border-amber-500/20"
                          title="Buy Book on Amazon"
                        >
                          <span>🛒</span>
                          <span>Buy</span>
                        </a>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 3: CATALOG */}
          {activeTab === "catalog" && (
            <div className="space-y-6 text-left">
              <div>
                <h2 className={`text-2xl font-extrabold ${isDark ? "text-white" : "text-slate-900"}`}>Search & Catalog Engine</h2>
                <p className="text-slate-400 text-xs mt-1">Fuzzy keyword search, genre filtering, and semantic book vector match APIs.</p>
              </div>

              <div className={`flex flex-col sm:flex-row gap-4 p-4 rounded-2xl border ${isDark ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200/50"}`}>
                <input 
                  type="text" 
                  placeholder="Search 'books like Atomic Habits' or 'productivity'..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className={`flex-grow border px-4 py-2.5 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 text-sm ${
                    isDark ? "bg-slate-950 border-slate-800 text-slate-100 placeholder-slate-650" : "bg-slate-50 border-slate-200/60 text-slate-800"
                  }`}
                />
                <select 
                  value={genreFilter}
                  onChange={(e) => setGenreFilter(e.target.value)}
                  className={`border px-4 py-2.5 rounded-xl focus:outline-none text-sm ${
                    isDark ? "bg-slate-955 border-slate-800 text-slate-300" : "bg-slate-50 border-slate-200/60 text-slate-700"
                  }`}
                >
                  <option value="">All Genres ({books.length})</option>
                  <option value="Fantasy">Fantasy</option>
                  <option value="Sci-Fi">Sci-Fi</option>
                  <option value="Self-Help">Self-Help</option>
                  <option value="Productivity">Productivity</option>
                  <option value="Mystery & Thriller">Mystery & Thriller</option>
                  <option value="Classics">Classics</option>
                  <option value="Fiction">Fiction</option>
                  <option value="Computer Science">Computer Science</option>
                </select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-4 gap-6">
                {books
                  .filter(b => b.title.toLowerCase().includes(searchQuery.toLowerCase()) || b.author.toLowerCase().includes(searchQuery.toLowerCase()))
                  .filter(b => !genreFilter || (b.genres && b.genres.toLowerCase().includes(genreFilter.toLowerCase())))
                  .map((book) => (
                    <div key={book.id} className={`border p-5 rounded-2xl space-y-4 hover:shadow-md transition-all duration-300 flex flex-col justify-between ${
                      isDark ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200/50"
                    }`}>
                      <div 
                        onClick={() => handleOpenDetails(book)}
                        className={`w-full h-36 rounded-xl flex items-center justify-center font-bold text-lg overflow-hidden cursor-pointer hover:opacity-90 transition-all ${
                          isDark ? "bg-slate-850 text-slate-600" : "bg-slate-50 text-slate-400"
                        }`}
                      >
                        {book.image_url_m ? (
                          <img src={book.image_url_m} alt={book.title} className="w-full h-full object-cover" />
                        ) : (
                          "📖"
                        )}
                      </div>
                      <div className="space-y-1">
                        <span className="bg-blue-500/10 text-blue-600 dark:text-blue-400 text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded">
                          {book.genres || "Fiction"}
                        </span>
                        <h4 
                          onClick={() => handleOpenDetails(book)}
                          className="font-bold text-sm line-clamp-1 cursor-pointer hover:text-blue-550 transition-colors"
                        >
                          {book.title}
                        </h4>
                        <p className="text-xs text-slate-400">{book.author}</p>
                      </div>
                      
                      <div className="flex gap-2 pt-2">
                        <button 
                          onClick={() => handleOpenDetails(book)}
                          className={`flex-1 py-2 border text-xs font-semibold rounded-xl transition-all ${
                            isDark ? "bg-slate-955 border-slate-800 hover:bg-slate-800 text-slate-200" : "bg-slate-50 border-slate-200/60 hover:bg-slate-100 text-slate-700"
                          }`}
                        >
                          Details
                        </button>
                        <a 
                          href={getAmazonBuyUrl(book.title, book.author)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-3 py-2 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-700 dark:text-amber-400 text-xs font-bold rounded-xl transition-all flex items-center gap-1"
                          title="Buy Book on Amazon"
                        >
                          <span>🛒</span>
                          <span>Buy</span>
                        </a>
                      </div>
                    </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 4: AI READING COACH */}
          {activeTab === "coach" && (
            <div className="space-y-6 text-left">
              <div>
                <h2 className={`text-2xl font-extrabold ${isDark ? "text-white" : "text-slate-900"}`}>AI Reading Coach & RAG Document Hub</h2>
                <p className="text-slate-400 text-xs mt-1">Upload PDF summaries, extract flashcards, generate study notes, and query documents.</p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className={`border p-6 rounded-2xl space-y-6 ${isDark ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200/50"}`}>
                  <div>
                    <h3 className="font-bold text-sm">RAG Document Vectorizer</h3>
                    <p className="text-xs text-slate-400 mt-1">Extract semantic embeddings from files into FAISS vectors.</p>
                  </div>
                  
                  <form onSubmit={handlePdfUpload} className="space-y-4">
                    <input 
                      type="file" 
                      accept=".pdf"
                      onChange={(e) => setPdfFile(e.target.files ? e.target.files[0] : null)}
                      className={`w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold ${
                        isDark ? "file:bg-slate-800 file:text-blue-400 hover:file:bg-slate-750" : "file:bg-blue-50 file:text-blue-600 hover:file:bg-blue-100"
                      }`}
                    />
                    <button 
                      type="submit" 
                      disabled={isUploadingPdf}
                      className={`w-full py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-2 ${
                        isUploadingPdf ? "opacity-75 cursor-not-allowed" : ""
                      }`}
                    >
                      {isUploadingPdf ? (
                        <>
                          <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/></svg>
                          Parsing & Vectorizing PDF...
                        </>
                      ) : (
                        "Upload & Vectorize PDF"
                      )}
                    </button>
                  </form>

                  {ragDoc && (
                    <div className={`p-4 rounded-xl space-y-4 border ${isDark ? "bg-slate-950 border-slate-855" : "bg-slate-50 border-slate-100"}`}>
                      <p className="text-xs text-slate-300 flex items-center gap-1.5">
                        <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span> 
                        <span><strong>Active Document:</strong> {ragDoc.filename}</span>
                      </p>
                      
                      <form onSubmit={handleRagQuery} className="space-y-2">
                        <input 
                          type="text" 
                          placeholder="Ask a question from this PDF document..."
                          value={ragQueryText}
                          onChange={(e) => setRagQueryText(e.target.value)}
                          className={`w-full border px-3 py-2 rounded-lg text-xs focus:outline-none ${
                            isDark ? "bg-slate-900 border-slate-850 text-slate-200" : "bg-white border-slate-200/80 text-slate-800"
                          }`}
                        />
                        <button 
                          type="submit" 
                          disabled={isQueryingRag}
                          className="w-full py-1.5 bg-blue-600 hover:bg-blue-750 text-white text-xs font-bold rounded-lg transition-all flex items-center justify-center gap-1.5"
                        >
                          {isQueryingRag ? "Vector Searching..." : "Query Document"}
                        </button>
                      </form>

                      {ragAnswer && (
                        <div className="space-y-2">
                          <div className={`p-3 rounded-lg border text-[11px] leading-relaxed whitespace-pre-line ${
                            isDark ? "bg-slate-900 border-slate-800 text-slate-300" : "bg-white border-slate-150 text-slate-700 shadow-inner"
                          }`}>
                            {ragAnswer}
                          </div>
                          
                          {ragSources.length > 0 && (
                            <div className="space-y-1">
                              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Retrieved Vector Chunks:</span>
                              {ragSources.map((src, i) => (
                                <div key={i} className="text-[10px] p-2 rounded bg-blue-500/10 border border-blue-500/20 text-blue-600 dark:text-blue-400">
                                  {src}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className={`lg:col-span-2 border rounded-2xl p-6 flex flex-col h-[460px] ${
                  isDark ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200/50"
                }`}>
                  <div className={`border-b pb-4 mb-4 ${isDark ? "border-slate-800" : "border-slate-100"}`}>
                    <h3 className="font-bold text-sm">AI Reading Assistant</h3>
                    <p className="text-xs text-slate-400 mt-1">Ask questions about book summaries, character notes, or core concepts.</p>
                  </div>
                  
                  <div className="flex-grow overflow-y-auto space-y-4 pr-2 scrollbar-thin text-left">
                    {chatMessages.length === 0 ? (
                      <div className="h-full flex items-center justify-center text-xs text-slate-400">
                        No active queries. Type below to consult your AI Coach.
                      </div>
                    ) : (
                      chatMessages.map((msg, i) => (
                        <div key={i} className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}>
                          <div className={`max-w-md p-3.5 rounded-2xl text-xs leading-relaxed ${
                            msg.sender === "user" 
                              ? "bg-blue-600 text-white font-semibold shadow-sm" 
                              : `${isDark ? "bg-slate-955 border border-slate-850 text-slate-200" : "bg-slate-100 text-slate-800"}`
                          }`}>
                            {msg.text}
                          </div>
                        </div>
                      ))
                    )}
                  </div>

                  <form onSubmit={handleCoachChat} className={`flex gap-2 border-t pt-4 mt-4 ${isDark ? "border-slate-800" : "border-slate-100"}`}>
                    <input 
                      type="text" 
                      placeholder="Ask details: 'What is systems thinking?'..."
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      className={`flex-grow border px-4 py-2 rounded-xl text-xs focus:outline-none ${
                        isDark ? "bg-slate-950 border-slate-800 text-slate-100" : "bg-slate-50 border-slate-200/80 text-slate-850"
                      }`}
                    />
                    <button type="submit" className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl transition-all">
                      Send
                    </button>
                  </form>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: ADMIN PORTAL */}
          {activeTab === "admin" && (
            <div className="space-y-6 text-left">
              <div>
                <h2 className={`text-2xl font-extrabold ${isDark ? "text-white" : "text-slate-900"}`}>Admin Management & Metrics</h2>
                <p className="text-slate-400 text-xs mt-1">Observe telemetry statistics, click-through rates (CTR), and A/B test results.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className={`border p-5 rounded-2xl ${isDark ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200/50"}`}>
                  <span className="text-xs text-slate-400 uppercase tracking-widest font-bold">Daily Active Users</span>
                  <h3 className="text-2xl font-black pt-2" suppressHydrationWarning>{formatNum(platformStats.dau)}</h3>
                  <span className="text-[10px] text-slate-500 font-semibold block mt-1">Real session history</span>
                </div>
                <div className={`border p-5 rounded-2xl ${isDark ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200/50"}`}>
                  <span className="text-xs text-slate-400 uppercase tracking-widest font-bold">Recommendation CTR</span>
                  <h3 className="text-2xl font-black pt-2" suppressHydrationWarning>{platformStats.recommendation_ctr.toFixed(1)}%</h3>
                  <span className="text-[10px] text-slate-500 font-semibold block mt-1">Real recommendation feedback</span>
                </div>
                <div className={`border p-5 rounded-2xl ${isDark ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200/50"}`}>
                  <span className="text-xs text-slate-400 uppercase tracking-widest font-bold">Active Challenges</span>
                  <h3 className="text-2xl font-black pt-2" suppressHydrationWarning>{user?.reading_challenge_count || 0}</h3>
                  <span className="text-[10px] text-slate-500 block mt-1">Registered challenge count</span>
                </div>
                <div className={`border p-5 rounded-2xl ${isDark ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200/50"}`}>
                  <span className="text-xs text-slate-400 uppercase tracking-widest font-bold">Total Catalog Books</span>
                  <h3 className="text-2xl font-black pt-2" suppressHydrationWarning>{formatNum(platformStats.total_books)}</h3>
                  <span className="text-[10px] text-slate-500 block mt-1">Seeded database items</span>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className={`border p-6 rounded-2xl space-y-4 ${isDark ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200/50"}`}>
                  <div>
                    <h4 className="font-bold text-sm">A/B Testing Model CTR Efficiency</h4>
                    <p className="text-xs text-slate-400">Comparing recommendation models in active production.</p>
                  </div>
                  
                  <div className={`h-60 flex items-end justify-around border-b border-l pb-4 pl-4 pt-4 ${isDark ? "border-slate-800" : "border-slate-200"}`}>
                    {ctrByModel.length > 0 ? (
                      ctrByModel.map((m, idx) => (
                        <div key={idx} className="flex flex-col items-center gap-2 w-16">
                          <div 
                            className={`w-full rounded-t-lg transition-all duration-500 ${
                              idx === 0 ? "bg-blue-500" : idx === 1 ? "bg-purple-500" : idx === 2 ? "bg-emerald-500" : "bg-amber-500"
                            }`} 
                            style={{ height: `${Math.min(180, Math.max(m.value > 0 ? 8 : 2, m.value * 4))}px` }}
                          ></div>
                          <span className="text-[9px] text-slate-400 text-center">{m.label.split(" ")[0]} ({m.value.toFixed(1)}%)</span>
                        </div>
                      ))
                    ) : (
                      <div className="h-full w-full flex items-center justify-center text-xs text-slate-400">
                        0.0% CTR (No feedback click logs recorded yet)
                      </div>
                    )}
                  </div>
                </div>

                <div className={`border p-6 rounded-2xl space-y-4 ${isDark ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200/50"}`}>
                  <div>
                    <h4 className="font-bold text-sm">Monthly Active Engagement (MAU)</h4>
                    <p className="text-xs text-slate-400">Visualizing registered user sessions tracking history.</p>
                  </div>
                  
                  <div className={`h-60 relative border-b border-l pb-4 pl-4 pt-4 ${isDark ? "border-slate-800" : "border-slate-200"}`}>
                    <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                      <path 
                        d="M 0 90 Q 20 60, 40 70 T 80 20 T 100 10" 
                        fill="none" 
                        stroke="url(#sky-grad)" 
                        strokeWidth="3" 
                        strokeLinecap="round"
                      />
                      <path 
                        d="M 0 90 Q 20 60, 40 70 T 80 20 T 100 10 L 100 100 L 0 100 Z" 
                        fill="url(#sky-area)" 
                        opacity="0.1"
                      />
                      <defs>
                        <linearGradient id="sky-grad" x1="0" y1="0" x2="1" y2="0">
                          <stop offset="0%" stopColor="#3b82f6" />
                          <stop offset="100%" stopColor="#8b5cf6" />
                        </linearGradient>
                        <linearGradient id="sky-area" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#3b82f6" />
                          <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
                        </linearGradient>
                      </defs>
                    </svg>
                    <div className="absolute bottom-2 left-4 right-2 flex justify-between text-[8px] text-slate-400">
                      <span>Jan</span>
                      <span>Mar</span>
                      <span>May</span>
                      <span>Jul</span>
                      <span>Sep</span>
                      <span>Nov</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 6: AUTHENTICATION */}
          {activeTab === "auth" && (
            <div className={`max-w-md mx-auto border rounded-3xl p-8 shadow-md space-y-6 text-left ${
              isDark ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200/50"
            }`}>
              <div className="text-center">
                <h2 className="text-xl font-bold">{isRegistering ? "Create Profile" : "Connect to NextGen Reads"}</h2>
                <p className="text-xs text-slate-400 mt-1">Unlock streams logs, streaks, and hybrid recommender vectors.</p>
              </div>

              <form onSubmit={isRegistering ? handleRegister : handleLogin} className="space-y-4">
                {isRegistering && (
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Full Name</label>
                    <input 
                      type="text" 
                      required 
                      value={authName}
                      onChange={(e) => setAuthName(e.target.value)}
                      className={`w-full border px-4 py-2.5 rounded-xl text-xs focus:outline-none ${
                        isDark ? "bg-slate-950 border-slate-800 text-slate-100" : "bg-slate-550/20 border-slate-200"
                      }`}
                      placeholder="Enter name"
                    />
                  </div>
                )}
                
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Email Address</label>
                  <input 
                    type="email" 
                    required 
                    value={authEmail}
                    onChange={(e) => setAuthEmail(e.target.value)}
                    className={`w-full border px-4 py-2.5 rounded-xl text-xs focus:outline-none ${
                      isDark ? "bg-slate-955 border-slate-800 text-slate-100" : "bg-slate-550/20 border-slate-200"
                    }`}
                    placeholder="name@example.com"
                  />
                </div>

                <div>
                  <label className="text-xs text-slate-400 block mb-1">Secure Password</label>
                  <input 
                    type="password" 
                    required 
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                    className={`w-full border px-4 py-2.5 rounded-xl text-xs focus:outline-none ${
                      isDark ? "bg-slate-955 border-slate-800 text-slate-100" : "bg-slate-550/20 border-slate-200"
                    }`}
                    placeholder="••••••••"
                  />
                </div>

                {isRegistering && (
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Favorite Genres (Semicolon separated)</label>
                    <input 
                      type="text" 
                      value={authGenres}
                      onChange={(e) => setAuthGenres(e.target.value)}
                      className={`w-full border px-4 py-2.5 rounded-xl text-xs focus:outline-none ${
                        isDark ? "bg-slate-955 border-slate-800 text-slate-100" : "bg-slate-550/20 border-slate-200"
                      }`}
                      placeholder="Fiction;Sci-Fi;Productivity"
                    />
                  </div>
                )}

                <button type="submit" className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl transition-all shadow-md">
                  {isRegistering ? "Register Profile" : "Verify Credentials"}
                </button>
              </form>

              <div className="relative flex items-center justify-center my-6">
                <div className={`absolute inset-0 border-t ${isDark ? "border-slate-800" : "border-slate-200"}`}></div>
                <span className={`relative px-4 text-[9px] text-slate-400 uppercase tracking-widest font-bold ${isDark ? "bg-slate-900" : "bg-white"}`}>Or Connect with</span>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <button onClick={() => alert("Google OAuth provider simulation activated.")} className={`py-2.5 border text-xs font-semibold rounded-xl transition-all ${
                  isDark ? "bg-slate-955 border-slate-800 hover:bg-slate-850 text-slate-350" : "bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-650"
                }`}>
                  Google
                </button>
                <button onClick={() => alert("GitHub OAuth provider simulation activated.")} className={`py-2.5 border text-xs font-semibold rounded-xl transition-all ${
                  isDark ? "bg-slate-955 border-slate-800 hover:bg-slate-850 text-slate-350" : "bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-650"
                }`}>
                  GitHub
                </button>
              </div>

              <div className="text-center pt-4">
                <button 
                  onClick={() => setIsRegistering(!isRegistering)}
                  className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                >
                  {isRegistering ? "Already have a profile? Sign In" : "Need an profile? Register here"}
                </button>
              </div>
            </div>
          )}

        </div>

        {/* FOOTER */}
        <footer className={`border-t py-8 text-center text-xs text-slate-400 transition-colors duration-300 ${
          isDark ? "bg-[#080c14]/40 border-slate-850 text-slate-500" : "bg-slate-50/50 border-slate-200/50 text-slate-450"
        }`}>
          <p>© 2026 Book Recommendation System platform. Production deployment ready.</p>
          <p className="pt-2 text-[10px] text-slate-500">Built using Next.js 16 + FastAPI 0.139 + Scikit-Learn Hybrid Recommendation Systems</p>
        </footer>

      </main>

      {/* Book Details Modal */}
      {detailBook && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-955/60 backdrop-blur-md transition-opacity duration-300">
          <div 
            className={`relative max-w-2xl w-full rounded-3xl shadow-2xl overflow-hidden transform transition-all duration-300 scale-100 p-6 md:p-8 ${
              isDark ? "bg-slate-900 border border-slate-800 text-white" : "bg-white border border-slate-200 text-slate-900"
            }`}
          >
            {/* Close Button */}
            <button 
              onClick={() => setDetailBook(null)}
              className="absolute top-6 right-6 p-2 rounded-full hover:bg-slate-200/50 dark:hover:bg-slate-800/50 transition-colors focus:outline-none"
              aria-label="Close details"
            >
              <svg className="w-5 h-5 text-slate-500 dark:text-slate-400" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            {/* Modal Body */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
              {/* Left Column: Cover Image */}
              <div className="md:col-span-1 flex flex-col items-center justify-start gap-4">
                <div className={`w-full h-64 md:h-72 rounded-2xl flex items-center justify-center font-bold text-3xl overflow-hidden shadow-lg border ${
                  isDark ? "bg-slate-850 border-slate-800 text-slate-600" : "bg-slate-50 border-slate-100 text-slate-400"
                }`}>
                  {detailBook.image_url_m || detailBook.image_url_l ? (
                    <img 
                      src={detailBook.image_url_l || detailBook.image_url_m} 
                      alt={detailBook.title} 
                      className="w-full h-full object-cover" 
                    />
                  ) : (
                    <span className="text-5xl">📖</span>
                  )}
                </div>
                {detailBook.isbn && (
                  <p className="text-[10px] tracking-wide uppercase text-slate-400 font-semibold font-mono">
                    ISBN: {detailBook.isbn}
                  </p>
                )}
                {detailBook.publisher && (
                  <p className="text-[10px] text-slate-400 text-center">
                    Pub: {detailBook.publisher}
                  </p>
                )}
              </div>

              {/* Right Column: Title, Author, Ratings, Description */}
              <div className="md:col-span-2 flex flex-col justify-between space-y-4">
                <div>
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    {(detailBook.genres || "Fiction").split(";").map((g, i) => (
                      <span key={i} className="bg-blue-500/10 border border-blue-500/20 text-blue-600 dark:text-blue-400 text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-md">
                        {g.trim()}
                      </span>
                    ))}
                  </div>

                  <h2 className="text-2xl font-black tracking-tight leading-tight mb-1 pr-6">
                    {detailBook.title}
                  </h2>
                  <p className="text-sm font-semibold text-slate-500 dark:text-slate-400">
                    by {detailBook.author}
                  </p>

                  {/* Rating Section */}
                  <div className="flex items-center gap-2 mt-3">
                    <div className="flex text-amber-400 text-sm">
                      {Array.from({ length: 5 }, (_, index) => {
                        const starValue = index + 1;
                        const rating = detailBook.rating_avg || 0;
                        return (
                          <span key={index}>
                            {rating >= starValue ? "★" : rating >= starValue - 0.5 ? "⯪" : "☆"}
                          </span>
                        );
                      })}
                    </div>
                    <span className="text-xs font-bold text-slate-700 dark:text-slate-200">
                      {detailBook.rating_avg ? detailBook.rating_avg.toFixed(1) : "0.0"}
                    </span>
                    <span className="text-[10px] text-slate-400">
                      ({detailBook.rating_count || 0} reviews)
                    </span>
                  </div>

                  {/* Description */}
                  <div className="mt-4">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                      About the book
                    </h4>
                    <p className={`text-xs leading-relaxed max-h-36 overflow-y-auto pr-1 scrollbar-thin ${
                      isDark ? "text-slate-300" : "text-slate-600"
                    }`}>
                      {detailBook.description || "No description available for this catalog item. Experience a hybrid pipeline workflow to recommend and read books with personalized AI insights."}
                    </p>
                  </div>
                </div>

                {/* Explainability insights */}
                {detailBook.explainability && (
                  <div className={`p-4 rounded-2xl border ${isDark ? "bg-slate-955 border-slate-850" : "bg-slate-50 border-slate-100"}`}>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-[11px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider">
                        AI Recommendation Insights
                      </span>
                      <span className="text-xs font-bold text-emerald-500">
                        Confidence: {Math.round(detailBook.explainability.confidence_score * 100)}%
                      </span>
                    </div>
                    <p className="text-[10px] leading-relaxed mb-3 text-slate-400">
                      <strong>Why Recommended:</strong> {detailBook.explainability.why}
                    </p>
                    <div className="grid grid-cols-2 gap-3 text-[9px] text-slate-400">
                      <div>
                        <div className="w-full bg-slate-200 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden mb-1">
                          <div className="bg-blue-500 h-full" style={{ width: `${detailBook.explainability.genre_similarity * 100}%` }}></div>
                        </div>
                        Genre Match: {Math.round(detailBook.explainability.genre_similarity * 100)}%
                      </div>
                      <div>
                        <div className="w-full bg-slate-200 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden mb-1">
                          <div className="bg-purple-500 h-full" style={{ width: `${detailBook.explainability.reader_overlap * 100}%` }}></div>
                        </div>
                        Reader Overlap: {Math.round(detailBook.explainability.reader_overlap * 100)}%
                      </div>
                      <div>
                        <div className="w-full bg-slate-200 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden mb-1">
                          <div className="bg-emerald-500 h-full" style={{ width: `${detailBook.explainability.semantic_similarity * 100}%` }}></div>
                        </div>
                        Semantic Sim: {Math.round(detailBook.explainability.semantic_similarity * 100)}%
                      </div>
                      <div>
                        <div className="w-full bg-slate-200 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden mb-1">
                          <div className="bg-amber-500 h-full" style={{ width: `${detailBook.explainability.popularity_score * 100}%` }}></div>
                        </div>
                        Popularity: {Math.round(detailBook.explainability.popularity_score * 100)}%
                      </div>
                    </div>
                  </div>
                )}

                {/* BUY BOOK REDIRECT SECTION */}
                <div className={`p-4 rounded-2xl border space-y-2 ${isDark ? "bg-slate-955 border-slate-850" : "bg-slate-50 border-slate-200/60"}`}>
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold text-amber-600 dark:text-amber-400 uppercase tracking-wider flex items-center gap-1">
                      <span>🛒</span>
                      <span>Buy This Book Online:</span>
                    </span>
                    <span className="text-[10px] text-slate-400">Redirects to store</span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 pt-1">
                    <a 
                      href={getAmazonBuyUrl(detailBook.title, detailBook.author)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-2 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-700 dark:text-amber-400 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-1.5 text-center"
                    >
                      <span>📦</span>
                      <span>Amazon</span>
                    </a>

                    <a 
                      href={getFlipkartBuyUrl(detailBook.title, detailBook.author)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-2 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 text-blue-600 dark:text-blue-400 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-1.5 text-center"
                    >
                      <span>🛍️</span>
                      <span>Flipkart</span>
                    </a>

                    <a 
                      href={getGoogleBooksUrl(detailBook.title, detailBook.author)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-2 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-1.5 text-center"
                    >
                      <span>🔍</span>
                      <span>Google</span>
                    </a>
                  </div>
                </div>

                {/* Modal Footer Controls */}
                <div className={`flex flex-wrap gap-3 pt-4 border-t ${isDark ? "border-slate-800" : "border-slate-100"}`}>
                  <button 
                    onClick={() => { 
                      setSelectedBook(detailBook); 
                      setActiveTab("coach"); 
                      loadQuiz(detailBook.id); 
                      loadPlan(detailBook.id); 
                      setDetailBook(null);
                    }} 
                    className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold flex-1 shadow-md shadow-blue-500/10 hover:shadow-blue-500/25 transition-all flex items-center justify-center gap-1.5"
                  >
                    <span>💬</span>
                    <span>Open Study Coach</span>
                  </button>
                  
                  <button 
                    onClick={() => {
                      handleAddToContextInModal(detailBook.title);
                      setIsAddingToContext(true);
                      setTimeout(() => setIsAddingToContext(false), 1500);
                    }} 
                    className={`px-4 py-2.5 rounded-xl text-xs font-semibold border flex items-center justify-center gap-1.5 transition-all ${
                      sessionContext.includes(detailBook.title)
                        ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400 cursor-default"
                        : "border-blue-500/20 bg-blue-500/5 text-blue-600 dark:text-blue-400 hover:bg-blue-500/10"
                    }`}
                  >
                    {sessionContext.includes(detailBook.title) ? (
                      <>
                        <span>✓</span>
                        <span>In Context</span>
                      </>
                    ) : isAddingToContext ? (
                      <>
                        <span className="animate-ping">●</span>
                        <span>Adding...</span>
                      </>
                    ) : (
                      <>
                        <span>+</span>
                        <span>Add to Context</span>
                      </>
                    )}
                  </button>

                  <button 
                    onClick={() => setDetailBook(null)} 
                    className={`px-4 py-2.5 rounded-xl border text-xs font-semibold transition-all ${
                      isDark 
                        ? "bg-slate-800 border-slate-700 hover:bg-slate-750 text-slate-200" 
                        : "bg-slate-100 border-slate-200/60 hover:bg-slate-200 text-slate-700"
                    }`}
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
