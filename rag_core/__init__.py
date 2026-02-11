"""
rag_core - 可移植的 RAG 模組

此套件設計為獨立可移植，可直接整合到任何 Python 專案。

主要元件：
- embeddings: 嵌入模型抽象層
- chunking: 文件分塊策略
- retrievers: 檢索器 (Dense/Sparse/Hybrid)
- rerankers: 重排序器
- ingest: 文件處理 Pipeline

使用方式:
    from rag_core import HybridRetriever, BGEM3Embedding, BGEReranker
    
    retriever = HybridRetriever(
        embedding=BGEM3Embedding(),
        reranker=BGEReranker()
    )
    results = await retriever.retrieve("你的查詢", top_k=5)
"""

from .config import RAGConfig
from .embeddings import EmbeddingProvider, BGEM3Embedding
from .retrievers import Retriever, RetrievalResult, DenseRetriever, SparseRetriever, HybridRetriever
from .rerankers import Reranker, BGEReranker
from .ingest import DocumentLoader, MultimodalIngestor

__version__ = "0.1.0"
__all__ = [
    "RAGConfig",
    "EmbeddingProvider",
    "BGEM3Embedding",
    "Retriever",
    "RetrievalResult",
    "DenseRetriever",
    "SparseRetriever",
    "HybridRetriever",
    "Reranker",
    "BGEReranker",
    "DocumentLoader",
    "MultimodalIngestor",
]
