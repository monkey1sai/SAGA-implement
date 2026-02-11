# 🚧 Current Task: sglangRAG 重構 - 移除語音、加入 RAG

**Last Updated**: 2026-02-02  
**Worker**: GitHub Copilot Agent

## 🎯 Objective
將專案從「語音對話系統」重構為「RAG 增強聊天系統」：
1. 移除所有 TTS/STT 語音功能
2. 建立獨立可移植的 `rag_core/` 套件
3. 改寫前端為純文字聊天介面
4. 整合 RAG 到 orchestrator

## ✅ Completed Tasks

### 1. 規劃架構：解耦 RAG 模組設計
- 設計抽象介面架構（EmbeddingProvider, Retriever, Reranker, DocumentLoader）
- 決定使用 Dense + Sparse + Rerank 混合檢索策略
- 確認不實作 GraphRAG（基礎版）

### 2. 建立獨立 RAG 套件骨架 (`rag_core/`)
- `rag_core/__init__.py` - 套件匯出
- `rag_core/config.py` - RAGConfig 設定類
- `rag_core/embeddings/` - BGE-M3 嵌入實作
- `rag_core/retrievers/` - Dense + Sparse + Hybrid 檢索器
- `rag_core/rerankers/` - BGE 重排序
- `rag_core/ingest/` - PDF/DOCX/TXT 文件處理
- `rag_core/server.py` - FastAPI 獨立服務
- `rag_core/pyproject.toml` - pip 套件設定

### 3. 移除語音相關模組 (TTS/STT)
- 刪除 `ws_gateway_tts/` 整個目錄
- 刪除 `docker/ws_gateway_tts.Dockerfile`
- 更新 `docker-compose.yml` 移除 TTS 服務

### 4. 改寫 web_client 聊天介面
- `web_client/src/App.jsx` - 主聊天介面
- `web_client/src/components/MessageList.jsx`
- `web_client/src/components/InputBar.jsx`
- `web_client/src/components/DocumentUpload.jsx`
- `web_client/src/style.css` - 深色主題樣式

### 5. 整合 RAG 到 orchestrator
- 重寫 `orchestrator/server.py`
- 新增 RAG 查詢功能、WebSocket 端點、對話上下文管理

### 6. 更新基礎設施
- `docker-compose.yml` - 新增 `rag` 服務
- `docker/rag.Dockerfile` - RAG 容器
- `docker/web_default.conf.template` - Nginx 路由

## 🔄 Pending Verification
- [ ] `docker compose build` 構建測試
- [ ] RAG 服務健康檢查 (`/health`)
- [ ] 前後端整合測試
- [ ] 文件上傳功能測試

## 🧠 Context & Thoughts
- RAG 模組設計為獨立套件，可 `pip install -e rag_core/`
- 參考 VoiceAgent 專案的 RAG 實作（BGE-M3 + BM25 + Rerank）
- 前端改用簡潔對話介面，移除 SAGA 流程圖

## 📝 Handoff Note
下一個 Agent 應該：
1. 執行 `docker compose build` 驗證所有服務可構建
2. 執行 `docker compose up -d` 啟動服務
3. 測試 RAG API (`curl http://localhost:8100/health`)
4. 測試 WebSocket 聊天功能
5. 確認文件上傳→RAG 檢索→LLM 回答流程正常
