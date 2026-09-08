import React from "react";

interface AIAssistantProps {
  chatMessages: any[];
  chatInput: string;
  setChatInput: (val: string) => void;
  handleCoachChat: (e: React.FormEvent) => void;
  ragDoc: any;
  pdfFile: any;
  setPdfFile: (file: any) => void;
  handlePdfUpload: (e: React.FormEvent) => void;
  isUploadingPdf: boolean;
}

export function AIAssistant({
  chatMessages,
  chatInput,
  setChatInput,
  handleCoachChat,
  ragDoc,
  pdfFile,
  setPdfFile,
  handlePdfUpload,
  isUploadingPdf
}: AIAssistantProps) {
  return (
    <div className="flex-col gap-lg" style={{ height: "100%" }}>
      {/* RAG Upload Area */}
      <div className="glass-panel" style={{ padding: "1.5rem" }}>
        <h3 style={{ fontSize: "1.25rem", marginBottom: "0.5rem" }}>Knowledge Base (RAG)</h3>
        <p className="text-muted" style={{ fontSize: "0.9rem", marginBottom: "1rem" }}>
          Upload a PDF book or document to chat with it directly.
        </p>
        <form onSubmit={handlePdfUpload} className="flex-row gap-sm items-center">
          <input 
            type="file" 
            accept="application/pdf"
            onChange={(e) => setPdfFile(e.target.files ? e.target.files[0] : null)}
            className="input-field"
            style={{ flex: 1 }}
          />
          <button type="submit" className="btn btn-primary" disabled={isUploadingPdf || !pdfFile}>
            {isUploadingPdf ? "Indexing..." : "Upload & Index"}
          </button>
        </form>
        {ragDoc && (
          <div className="badge badge-success" style={{ marginTop: "1rem" }}>
            Active Document: {ragDoc.filename}
          </div>
        )}
      </div>

      {/* Chat Window */}
      <div className="chat-window">
        <div className="chat-messages">
          {chatMessages.length === 0 ? (
            <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-muted)", fontStyle: "italic" }}>
              Start a conversation with the AI reading coach...
            </div>
          ) : (
            chatMessages.map((msg, i) => (
              <div key={i} className={`chat-bubble ${msg.sender === "user" ? "chat-bubble-user" : "chat-bubble-ai"}`}>
                {msg.text}
              </div>
            ))
          )}
        </div>
        <form onSubmit={handleCoachChat} className="chat-input-area">
          <input 
            type="text" 
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            placeholder="Ask your AI reading coach a question..."
            className="input-field"
            style={{ flex: 1 }}
          />
          <button type="submit" className="btn btn-primary">
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
