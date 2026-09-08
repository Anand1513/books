with open('src/app/page.tsx', 'r') as f:
    lines = f.readlines()

state_lines = lines[:596]

new_jsx = """
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
"""

imports = '''import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { StatCards } from "@/components/dashboard/StatCards";
import { BookCard } from "@/components/books/BookCard";
import { AIAssistant } from "@/components/chat/AIAssistant";
'''

state_lines.insert(4, imports)

with open('src/app/page.tsx', 'w') as f:
    f.writelines(state_lines)
    f.write(new_jsx)
