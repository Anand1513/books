import React, { useState } from "react";

interface HeaderProps {
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  notificationCount: number;
  setNotificationCount: (count: number) => void;
  user: any;
}

export function Header({
  searchQuery,
  setSearchQuery,
  activeTab,
  setActiveTab,
  notificationCount,
  setNotificationCount,
  user
}: HeaderProps) {
  const [showNotificationsMenu, setShowNotificationsMenu] = useState(false);

  return (
    <header className="top-header glass-panel" style={{ padding: "1rem 2rem", borderRadius: 0, borderTop: "none", borderLeft: "none", borderRight: "none", position: "sticky", top: 0, zIndex: 50, marginBottom: 0 }}>
      {/* Search */}
      <div style={{ flex: 1, maxWidth: "500px" }}>
        <input 
          type="text" 
          placeholder="Search books, authors, genres..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onClick={() => { if (activeTab !== "catalog" && activeTab !== "dashboard") setActiveTab("catalog"); }}
          className="input-field"
          style={{ width: "100%", borderRadius: "var(--radius-full)", paddingLeft: "1.5rem" }}
        />
      </div>

      {/* Actions */}
      <div className="flex-row items-center gap-md">
        {/* Notifications */}
        <div style={{ position: "relative" }}>
          <button 
            className="btn-secondary"
            style={{ borderRadius: "var(--radius-full)", padding: "0.5rem", position: "relative" }}
            onClick={() => {
              setShowNotificationsMenu(!showNotificationsMenu);
              if (notificationCount > 0) setNotificationCount(0);
            }}
          >
            🔔
            {notificationCount > 0 && (
              <span style={{ position: "absolute", top: -5, right: -5, background: "var(--secondary)", color: "white", borderRadius: "50%", padding: "0.1rem 0.4rem", fontSize: "0.7rem", fontWeight: "bold" }}>
                {notificationCount}
              </span>
            )}
          </button>

          {showNotificationsMenu && (
            <div className="glass-panel" style={{ position: "absolute", right: 0, top: "calc(100% + 10px)", width: "300px", padding: "1rem" }}>
              <div className="flex-row justify-between items-center" style={{ borderBottom: "1px solid var(--border-color)", paddingBottom: "0.5rem", marginBottom: "1rem" }}>
                <h4 style={{ margin: 0, fontSize: "0.9rem" }}>Notifications</h4>
                <span className="badge badge-success">Systems Operational</span>
              </div>
              <p className="text-muted text-sm text-center">
                🔔 No unread notifications. All recommendation algorithms up to date!
              </p>
            </div>
          )}
        </div>

        {/* Profile */}
        {user ? (
          <div className="flex-row items-center gap-sm">
            <span className="font-medium text-sm">Hi, {user.full_name || "Admin"}</span>
            <div style={{ width: "36px", height: "36px", borderRadius: "50%", background: "var(--primary)", display: "flex", alignItems: "center", justifyContent: "center", color: "white", fontWeight: "bold" }}>
              {user.full_name ? user.full_name.charAt(0) : "A"}
            </div>
          </div>
        ) : (
          <button className="btn btn-primary" onClick={() => setActiveTab("auth")}>
            Sign In
          </button>
        )}
      </div>
    </header>
  );
}
