# RAG Core

**可移植的 RAG (Retrieval-Augmented Generation) 模組**

此套件設計為獨立可移植，可直接整合到任何 Python 專案（如 VoiceAgent、sglangRAG 等）。

## 特點

- 🔌 **即插即用**：獨立套件，不依賴特定專案結構
- 🔍 **Hybrid Search**：結合 Dense (向量) + Sparse (BM25) 檢索
- 🎯 **Reranking**：使用 BGE Reranker 精排序
- 📄 **多格式支援**：PDF、DOCX、TXT、MD
- 🚀 **獨立服務**：可作為 FastAPI 服務獨立運行

## 安裝

```bash
# 基礎安裝
pip install -e ./rag_core

# 包含 PDF 支援
pip install -e "./rag_core[pdf]"

# 完整安裝
pip install -e "./rag_core[full]"
```

## 快速開始

### 作為 Python 套件使用

```python
from rag_core import HybridRetriever, BGEM3Embedding, DenseRetriever, SparseRetriever, BGEReranker

# 初始化元件
embedding = BGEM3Embedding()
dense = DenseRetriever(embedding=embedding)
sparse = SparseRetriever()
reranker = BGEReranker()

# 組合成 Hybrid Retriever
retriever = HybridRetriever(
    dense_retriever=dense,
    sparse_retriever=sparse,
    reranker=reranker,
)

# 新增文件
await retriever.add_documents([
    "這是第一份文件的內容...",
    "這是第二份文件的內容...",
])

# 檢索
results = await retriever.retrieve("你的查詢", top_k=5)
for r in results:
    print(f"[{r.score:.3f}] {r.text[:100]}...")
```

### 作為獨立服務運行

```bash
# 啟動 RAG 服務
uvicorn rag_core.server:app --host 0.0.0.0 --port 8100

# 或使用 CLI
rag-server
```

### API 端點

| 方法 | 端點 | 說明 |
|------|------|------|
| POST | `/search` | 檢索相關文件 |
| POST | `/documents` | 新增文件 |
| DELETE | `/documents` | 刪除文件 |
| POST | `/ingest/file` | 上傳並處理文件 |
| POST | `/ingest/directory` | 批次處理目錄 |
| GET | `/health` | 健康檢查 |

## 配置

透過環境變數設定：

```bash
# 嵌入模型
RAG_EMBEDDING_MODEL=BAAI/bge-m3
RAG_EMBEDDING_DEVICE=cuda

# 向量資料庫
RAG_VECTOR_DB_PATH=./data/chroma_db
RAG_COLLECTION_NAME=documents

# Reranker
RAG_RERANKER_MODEL=BAAI/bge-reranker-base

# 檢索
RAG_DEFAULT_TOP_K=5
```

## 架構

```
rag_core/
├── embeddings/     # 嵌入模型抽象層
├── retrievers/     # 檢索器 (Dense/Sparse/Hybrid)
├── rerankers/      # 重排序器
├── ingest/         # 文件處理 Pipeline
├── config.py       # 配置
└── server.py       # FastAPI 服務
```

## 移植到其他專案

1. 複製 `rag_core/` 資料夾到目標專案
2. 安裝依賴：`pip install -e ./rag_core`
3. 在程式碼中 import 使用：

```python
from rag_core import HybridRetriever, RAGConfig
```

## License

MIT
