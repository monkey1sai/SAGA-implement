import React, { useState, useRef, useEffect, useCallback } from "react";
import MessageList from "./components/MessageList.jsx";
import InputBar from "./components/InputBar.jsx";
import DocumentUpload from "./components/DocumentUpload.jsx";
import "./style.css";

/**
 * sglangRAG 主聊天介面
 * 
 * 設計參考 VoiceAgent 的純文字對話介面，支援：
 * - 即時文字對話（WebSocket）
 * - RAG 文件上傳與檢索增強
 * - 訊息串流顯示
 */

const defaultWsUrl = (() => {
  if (typeof window === "undefined") return "ws://localhost:9100/ws/chat";
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${window.location.host}/ws/chat`;
})();

const defaultRagUrl = (() => {
  if (typeof window === "undefined") return "http://localhost:8100";
  return `${window.location.protocol}//${window.location.host}/api/rag`;
})();

export default function App() {
  // 訊息列表
  const [messages, setMessages] = useState([
    {
      id: "welcome",
      role: "assistant",
      content: "你好！我是 sglangRAG 智慧助理。你可以上傳文件讓我學習，然後問我相關問題。",
      timestamp: new Date().toISOString(),
    },
  ]);
  
  // 連線狀態
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  // RAG 狀態
  const [ragEnabled, setRagEnabled] = useState(true);
  const [documentCount, setDocumentCount] = useState(0);
  
  // 設定
  const [showSettings, setShowSettings] = useState(false);
  const [wsUrl, setWsUrl] = useState(defaultWsUrl);
  const [ragUrl, setRagUrl] = useState(defaultRagUrl);
  
  // WebSocket 參考
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  
  // 自動滾動到底部
  const messagesEndRef = useRef(null);
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);
  
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);
  
  // WebSocket 連線管理
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    
    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      
      ws.onopen = () => {
        console.log("WebSocket 已連線");
        setIsConnected(true);
      };
      
      ws.onclose = () => {
        console.log("WebSocket 已斷線");
        setIsConnected(false);
        setIsLoading(false);
        
        // 自動重連
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log("嘗試重新連線...");
          connect();
        }, 3000);
      };
      
      ws.onerror = (error) => {
        console.error("WebSocket 錯誤:", error);
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleServerMessage(data);
        } catch (e) {
          console.error("解析訊息失敗:", e);
        }
      };
    } catch (error) {
      console.error("連線失敗:", error);
    }
  }, [wsUrl]);
  
  // 處理伺服器訊息
  const handleServerMessage = useCallback((data) => {
    switch (data.type) {
      case "llm_delta":
        // 串流增量更新
        setMessages((prev) => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg?.role === "assistant" && lastMsg?.streaming) {
            return [
              ...prev.slice(0, -1),
              { ...lastMsg, content: lastMsg.content + data.delta },
            ];
          }
          return prev;
        });
        break;
        
      case "llm_complete":
        // 回覆完成
        setMessages((prev) => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg?.role === "assistant" && lastMsg?.streaming) {
            return [
              ...prev.slice(0, -1),
              { ...lastMsg, streaming: false },
            ];
          }
          return prev;
        });
        setIsLoading(false);
        break;
        
      case "rag_context":
        // RAG 檢索到的上下文（可選顯示）
        console.log("RAG 上下文:", data.results);
        break;
        
      case "error":
        setMessages((prev) => [
          ...prev,
          {
            id: `error-${Date.now()}`,
            role: "system",
            content: `錯誤: ${data.message}`,
            timestamp: new Date().toISOString(),
          },
        ]);
        setIsLoading(false);
        break;
        
      default:
        console.log("未知訊息類型:", data);
    }
  }, []);
  
  // 自動連線
  useEffect(() => {
    connect();
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);
  
  // 發送訊息
  const sendMessage = useCallback((text) => {
    if (!text.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }
    
    // 新增用戶訊息
    const userMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };
    
    // 新增助理佔位訊息（串流中）
    const assistantMessage = {
      id: `assistant-${Date.now()}`,
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
      streaming: true,
    };
    
    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setIsLoading(true);
    
    // 發送到伺服器
    wsRef.current.send(JSON.stringify({
      type: "chat",
      text: text,
      use_rag: ragEnabled,
    }));
  }, [ragEnabled]);
  
  // 處理文件上傳成功
  const handleUploadSuccess = useCallback((result) => {
    setDocumentCount((prev) => prev + result.chunks);
    
    setMessages((prev) => [
      ...prev,
      {
        id: `system-${Date.now()}`,
        role: "system",
        content: `✅ 已成功處理文件「${result.filename}」，新增 ${result.chunks} 個知識片段。`,
        timestamp: new Date().toISOString(),
      },
    ]);
  }, []);
  
  // 清除對話
  const clearMessages = useCallback(() => {
    setMessages([
      {
        id: "welcome",
        role: "assistant",
        content: "對話已清除。有什麼我可以幫助你的嗎？",
        timestamp: new Date().toISOString(),
      },
    ]);
  }, []);
  
  return (
    <div className="app-container">
      {/* 頂部導航 */}
      <header className="app-header">
        <div className="header-left">
          <h1 className="app-title">sglangRAG</h1>
          <span className={`connection-status ${isConnected ? "connected" : "disconnected"}`}>
            {isConnected ? "● 已連線" : "○ 離線"}
          </span>
        </div>
        
        <div className="header-right">
          <label className="rag-toggle">
            <input
              type="checkbox"
              checked={ragEnabled}
              onChange={(e) => setRagEnabled(e.target.checked)}
            />
            <span>RAG 增強 {documentCount > 0 && `(${documentCount} 片段)`}</span>
          </label>
          
          <button
            className="icon-button"
            onClick={() => setShowSettings(!showSettings)}
            title="設定"
          >
            ⚙️
          </button>
          
          <button
            className="icon-button"
            onClick={clearMessages}
            title="清除對話"
          >
            🗑️
          </button>
        </div>
      </header>
      
      {/* 設定面板 */}
      {showSettings && (
        <div className="settings-panel">
          <div className="setting-item">
            <label>WebSocket URL</label>
            <input
              type="text"
              value={wsUrl}
              onChange={(e) => setWsUrl(e.target.value)}
            />
          </div>
          <div className="setting-item">
            <label>RAG API URL</label>
            <input
              type="text"
              value={ragUrl}
              onChange={(e) => setRagUrl(e.target.value)}
            />
          </div>
          <button onClick={connect}>重新連線</button>
        </div>
      )}
      
      {/* 主要內容區 */}
      <main className="app-main">
        {/* 訊息列表 */}
        <div className="messages-container">
          <MessageList messages={messages} />
          <div ref={messagesEndRef} />
        </div>
        
        {/* 輸入區 */}
        <div className="input-container">
          <DocumentUpload
            ragUrl={ragUrl}
            onUploadSuccess={handleUploadSuccess}
          />
          <InputBar
            onSend={sendMessage}
            disabled={!isConnected || isLoading}
            isLoading={isLoading}
          />
        </div>
      </main>
    </div>
  );
}
