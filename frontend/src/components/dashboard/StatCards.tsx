import React from "react";

interface StatCardsProps {
  platformStats: {
    total_users: number;
    total_books: number;
    total_ratings: number;
    recommendation_ctr: number;
    dau: number;
    mau: number;
  };
  formatNum: (num: number) => string;
}

export function StatCards({ platformStats, formatNum }: StatCardsProps) {
  return (
    <div className="grid-stats">
      {/* Card 1 */}
      <div className="glass-panel" style={{ padding: "1.5rem" }}>
        <div className="flex-row justify-between items-center" style={{ marginBottom: "1rem" }}>
          <div style={{ background: "rgba(99, 102, 241, 0.1)", color: "#6366f1", padding: "0.5rem", borderRadius: "0.5rem" }}>
            📚
          </div>
          <span className="badge badge-success">▲ 12.5%</span>
        </div>
        <div className="text-muted" style={{ fontSize: "0.8rem", marginBottom: "0.25rem" }}>Books in Catalog</div>
        <div className="font-bold" style={{ fontSize: "1.5rem" }} suppressHydrationWarning>
          {formatNum(platformStats.total_books)}
        </div>
      </div>

      {/* Card 2 */}
      <div className="glass-panel" style={{ padding: "1.5rem" }}>
        <div className="flex-row justify-between items-center" style={{ marginBottom: "1rem" }}>
          <div style={{ background: "rgba(59, 130, 246, 0.1)", color: "#3b82f6", padding: "0.5rem", borderRadius: "0.5rem" }}>
            ✨
          </div>
          <span className="badge badge-success">▲ 18.7%</span>
        </div>
        <div className="text-muted" style={{ fontSize: "0.8rem", marginBottom: "0.25rem" }}>Recommendations</div>
        <div className="font-bold" style={{ fontSize: "1.5rem" }} suppressHydrationWarning>
          {(platformStats.total_ratings / 1000).toFixed(1)}K
        </div>
      </div>

      {/* Card 3 */}
      <div className="glass-panel" style={{ padding: "1.5rem" }}>
        <div className="flex-row justify-between items-center" style={{ marginBottom: "1rem" }}>
          <div style={{ background: "rgba(236, 72, 153, 0.1)", color: "#ec4899", padding: "0.5rem", borderRadius: "0.5rem" }}>
            👥
          </div>
          <span className="badge badge-success">▲ 5.2%</span>
        </div>
        <div className="text-muted" style={{ fontSize: "0.8rem", marginBottom: "0.25rem" }}>Active Users</div>
        <div className="font-bold" style={{ fontSize: "1.5rem" }} suppressHydrationWarning>
          {formatNum(platformStats.total_users)}
        </div>
      </div>

      {/* Card 4 */}
      <div className="glass-panel" style={{ padding: "1.5rem" }}>
        <div className="flex-row justify-between items-center" style={{ marginBottom: "1rem" }}>
          <div style={{ background: "rgba(16, 185, 129, 0.1)", color: "#10b981", padding: "0.5rem", borderRadius: "0.5rem" }}>
            🎯
          </div>
          <span className="badge badge-primary">Steady</span>
        </div>
        <div className="text-muted" style={{ fontSize: "0.8rem", marginBottom: "0.25rem" }}>Recommendation CTR</div>
        <div className="font-bold" style={{ fontSize: "1.5rem" }} suppressHydrationWarning>
          {(platformStats.recommendation_ctr * 100).toFixed(1)}%
        </div>
      </div>
    </div>
  );
}
