import React from "react";

/**
 * 訊息列表元件
 * 
 * 顯示對話中的所有訊息，支援：
 * - 用戶訊息（靠右）
 * - 助理訊息（靠左）
 * - 系統訊息（置中）
 * - 串流中的訊息動畫
 */

export default function MessageList({ messages }) {
  return (
    <div className="message-list">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
    </div>
  );
}

function MessageBubble({ message }) {
  const { role, content, timestamp, streaming } = message;
  
  const roleClass = role === "user" ? "user" : role === "system" ? "system" : "assistant";
  
  // 格式化時間
  const timeStr = timestamp
    ? new Date(timestamp).toLocaleTimeString("zh-TW", {
        hour: "2-digit",
        minute: "2-digit",
      })
    : "";
  
  return (
    <div className={`message-bubble ${roleClass}`}>
      <div className="message-content">
        {content}
        {streaming && <span className="typing-indicator">▌</span>}
      </div>
      {timeStr && <div className="message-time">{timeStr}</div>}
    </div>
  );
}
