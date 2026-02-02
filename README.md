# sglangRAG

> 高效能 LLM 聊天系統，整合 RAG (Retrieval-Augmented Generation) 檢索增強功能

## 🚀 功能特色

- **SGLang 推論引擎** - 高效能 LLM 推論，支援 RadixAttention 與 Continuous Batching
- **RAG 檢索增強** - 混合搜尋（Dense + Sparse + Rerank）提升回答品質
- **即時串流** - WebSocket 即時串流回覆，低延遲使用者體驗
- **模組化設計** - RAG 模組可獨立部署，移植到任意專案

## 📦 專案結構

```
sglangRAG/
├── rag_core/           # 獨立 RAG 套件（可 pip install）
│   ├── embeddings/     # 嵌入模型（BGE-M3）
│   ├── retrievers/     # 檢索器（Dense, Sparse, Hybrid）
│   ├── rerankers/      # 重排序（BGE-Reranker）
│   ├── ingest/         # 文件處理（PDF, DOCX, TXT）
│   └── server.py       # FastAPI 獨立服務
├── orchestrator/       # 協調器服務
│   └── server.py       # WebSocket 聊天 + RAG 整合
├── web_client/         # React 前端
│   └── src/
│       ├── App.jsx
│       └── components/
├── docker/             # Docker 配置
└── docker-compose.yml
```

## 🛠️ 快速開始

### 前置需求

- Docker Desktop + NVIDIA Container Toolkit
- NVIDIA GPU（建議 8GB+ VRAM）
- Node.js 18+（前端開發）

### 1. 環境設定

```bash
cp .env.example .env
# 編輯 .env，設定 SGLANG_API_KEY, HF_TOKEN 等
```

### 2. 啟動服務

```bash
docker compose up -d
```

### 3. 存取介面

- **聊天介面**: http://localhost:8080
- **RAG API**: http://localhost:8100
- **SGLang API**: http://localhost:8082

## 📚 RAG 模組使用

### 獨立安裝

```bash
cd rag_core
pip install -e .
```

### Python 使用範例

```python
from rag_core import HybridRetriever, BGEM3Embedding, BGEReranker

# 初始化
embedding = BGEM3Embedding()
retriever = HybridRetriever(
    embedding_provider=embedding,
    persist_directory="./chroma_db",
)
reranker = BGEReranker()

# 新增文件
retriever.add_documents(["文件內容1", "文件內容2"])

# 檢索
results = retriever.search("查詢問題", top_k=5)

# 重排序
reranked = reranker.rerank("查詢問題", results, top_k=3)
```

### REST API

```bash
# 上傳文件
curl -X POST http://localhost:8100/ingest/file \
  -F "file=@document.pdf"

# 檢索
curl -X POST http://localhost:8100/search \
  -H "Content-Type: application/json" \
  -d '{"query": "問題內容", "top_k": 5}'
```

## 🔧 環境變數

| 變數 | 說明 | 預設值 |
|------|------|--------|
| `SGLANG_API_KEY` | SGLang API 金鑰 | (必填) |
| `SGLANG_MODEL` | 模型名稱 | `twinkle-ai/Llama-3.2-3B-F1-Instruct` |
| `RAG_SERVICE_URL` | RAG 服務位址 | `http://localhost:8100` |
| `RAG_EMBEDDING_MODEL` | 嵌入模型 | `BAAI/bge-m3` |
| `RAG_RERANK_MODEL` | 重排序模型 | `BAAI/bge-reranker-v2-m3` |

## 🏗️ 架構設計

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Frontend   │────▶│ Orchestrator │────▶│   SGLang    │
│  (React)    │     │  (aiohttp)   │     │   (LLM)     │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  RAG Service │
                    │  (FastAPI)   │
                    └──────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌─────────┐  ┌─────────┐  ┌─────────┐
        │ ChromaDB│  │  BM25   │  │ Reranker│
        │ (Dense) │  │(Sparse) │  │  (BGE)  │
        └─────────┘  └─────────┘  └─────────┘
```

## 📝 開發指南

### 前端開發

```bash
cd web_client
npm install
npm run dev
```

### RAG 服務開發

```bash
cd rag_core
pip install -e ".[dev]"
uvicorn server:app --reload --port 8100
```

## 📄 授權

MIT License
