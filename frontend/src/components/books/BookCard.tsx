import React from "react";

interface Book {
  id: number;
  title: string;
  author: string;
  image_url_m?: string;
  rating_avg: number;
  genres?: string;
}

interface BookCardProps {
  book: any;
  onClick: (book: any) => void;
}

export function BookCard({ book, onClick }: BookCardProps) {
  return (
    <div className="book-card" onClick={() => onClick(book)}>
      {book.image_url_m ? (
        <img src={book.image_url_m} alt={book.title} className="book-card-image" />
      ) : (
        <div className="book-card-image" style={{ background: "var(--bg-elevated)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-muted)" }}>
          No Image
        </div>
      )}
      <div className="book-card-content flex-col justify-end">
        <h3 style={{ fontSize: "1rem", margin: "0 0 0.25rem 0", textOverflow: "ellipsis", whiteSpace: "nowrap", overflow: "hidden" }} title={book.title}>
          {book.title}
        </h3>
        <p className="text-muted" style={{ fontSize: "0.8rem", margin: "0 0 0.5rem 0" }}>{book.author}</p>
        
        <div className="flex-row items-center justify-between">
          <span className="badge badge-primary" style={{ fontSize: "0.65rem" }}>
            {book.genres ? book.genres.split(",")[0] : "Fiction"}
          </span>
          <span style={{ fontSize: "0.8rem", fontWeight: "bold", color: "#fbbf24" }}>
            ★ {book.rating_avg.toFixed(1)}
          </span>
        </div>
      </div>
    </div>
  );
}
