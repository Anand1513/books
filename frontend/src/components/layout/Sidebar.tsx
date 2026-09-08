import React from "react";

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  isDark: boolean;
  setTheme: (theme: "light" | "dark") => void;
  user: any;
  handleLogout: () => void;
  fetchRecommendations: () => void;
}

export function Sidebar({
  activeTab,
  setActiveTab,
  isDark,
  setTheme,
  user,
  handleLogout,
  fetchRecommendations
}: SidebarProps) {
  const navLinks = [
    { id: "dashboard", label: "Dashboard", icon: "📊" },
    { id: "recommendations", label: "AI Recommendations", icon: "✨" },
    { id: "catalog", label: "Catalog", icon: "📚" },
    { id: "coach", label: "AI Reading Coach", icon: "🤖" },
    { id: "admin", label: "Admin Portal", icon: "⚙️" }
  ];

  return (
    <aside className="sidebar">
      <div className="flex-col gap-lg" style={{ padding: "0 1.5rem" }}>
        {/* Logo */}
        <div className="flex-row items-center gap-sm" style={{ marginBottom: "2rem" }}>
          <div style={{ fontSize: "2rem" }}>📚</div>
          <div>
            <h2 style={{ fontSize: "1.1rem", margin: 0 }}>NextGen Reads</h2>
            <p className="text-muted" style={{ fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "1px" }}>AI Engine</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-col gap-xs">
          {navLinks.map((link) => (
            <div
              key={link.id}
              className={`nav-item ${activeTab === link.id ? "active" : ""}`}
              onClick={() => {
                setActiveTab(link.id);
                if (link.id === "recommendations") fetchRecommendations();
              }}
            >
              <span className="nav-icon">{link.icon}</span>
              <span>{link.label}</span>
            </div>
          ))}
        </nav>
        
        {/* Pipeline Actions */}
        <div style={{ marginTop: "2rem" }}>
          <h4 className="text-muted" style={{ fontSize: "0.75rem", textTransform: "uppercase", marginBottom: "0.5rem" }}>Pipeline</h4>
          <div className="nav-item" onClick={() => { setActiveTab("recommendations"); fetchRecommendations(); }}>
             Generate Recs
          </div>
          <div className="nav-item" onClick={() => setActiveTab("coach")}>
             Upload RAG PDF
          </div>
        </div>
      </div>

      <div style={{ marginTop: "auto", padding: "1.5rem", borderTop: "1px solid var(--border-color)" }}>
        {/* Theme Toggle */}
        <div className="flex-row items-center justify-between" style={{ marginBottom: "1rem", cursor: "pointer" }} onClick={() => setTheme(isDark ? "light" : "dark")}>
          <span className="text-muted font-medium text-sm">Theme Mode</span>
          <span>{isDark ? "🌙 Dark" : "☀️ Light"}</span>
        </div>

        {/* User Card */}
        {user ? (
          <div className="glass-panel" style={{ padding: "1rem", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div>
              <div className="font-bold" style={{ fontSize: "0.9rem" }}>{user.full_name || "Admin"}</div>
              <div className="text-muted" style={{ fontSize: "0.75rem" }}>{user.email || "admin@nextgenreads.ai"}</div>
            </div>
            <button className="btn-ghost" onClick={handleLogout} title="Logout" style={{ padding: "0.25rem 0.5rem", color: "#ef4444" }}>
               Log out
            </button>
          </div>
        ) : (
          <button className="btn btn-primary" style={{ width: "100%" }} onClick={() => setActiveTab("auth")}>
            Sign In Account
          </button>
        )}
      </div>
    </aside>
  );
}
