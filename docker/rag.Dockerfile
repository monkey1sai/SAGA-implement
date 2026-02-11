# RAG Service Dockerfile
# 提供 Hybrid Search (Dense + Sparse + Rerank) 服務

FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 複製 RAG 核心模組
COPY rag_core/ /app/rag_core/

# 安裝 Python 依賴
RUN pip install --no-cache-dir \
    chromadb>=0.4.0 \
    rank-bm25>=0.2.2 \
    jieba>=0.42.1 \
    FlagEmbedding>=1.2.0 \
    fastapi>=0.100.0 \
    uvicorn>=0.23.0 \
    pydantic>=2.0.0 \
    python-multipart>=0.0.6 \
    pymupdf>=1.23.0 \
    python-docx>=1.0.0

# 建立資料目錄
RUN mkdir -p /data/chroma_db /data/uploads

# 暴露埠號
EXPOSE 8100

# 啟動服務
CMD ["python", "-m", "uvicorn", "rag_core.server:app", "--host", "0.0.0.0", "--port", "8100"]
