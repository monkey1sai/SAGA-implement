import React, { useState, useRef, useCallback } from "react";

/**
 * 輸入欄元件
 * 
 * 支援：
 * - 文字輸入
 * - Enter 發送（Shift+Enter 換行）
 * - 自動調整高度
 * - 發送中狀態
 */

export default function InputBar({ onSend, disabled, isLoading }) {
  const [text, setText] = useState("");
  const textareaRef = useRef(null);
  
  // 自動調整高度
  const adjustHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`;
    }
  }, []);
  
  const handleChange = useCallback((e) => {
    setText(e.target.value);
    adjustHeight();
  }, [adjustHeight]);
  
  const handleKeyDown = useCallback((e) => {
    // Enter 發送，Shift+Enter 換行
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, []);
  
  const handleSend = useCallback(() => {
    const trimmed = text.trim();
    if (trimmed && !disabled) {
      onSend(trimmed);
      setText("");
      
      // 重置高度
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  }, [text, disabled, onSend]);
  
  return (
    <div className="input-bar">
      <textarea
        ref={textareaRef}
        className="input-textarea"
        placeholder={disabled ? "連線中..." : "輸入訊息... (Enter 發送，Shift+Enter 換行)"}
        value={text}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        rows={1}
      />
      
      <button
        className={`send-button ${isLoading ? "loading" : ""}`}
        onClick={handleSend}
        disabled={disabled || !text.trim()}
        title="發送"
      >
        {isLoading ? (
          <span className="loading-spinner">⏳</span>
        ) : (
          <span>➤</span>
        )}
      </button>
    </div>
  );
}
