"""RAG 配置模組"""

from dataclasses import dataclass, field
from typing import List, Optional
import os


@dataclass
class RAGConfig:
    """
    RAG 系統配置
    
    可透過環境變數或直接傳入覆寫預設值。
    設計為可序列化，方便跨專案移植。
    """
    
    # 嵌入模型設定
    embedding_model: str = "BAAI/bge-m3"
    embedding_device: str = "cuda"
    embedding_batch_size: int = 32
    
    # 向量資料庫設定
    vector_db_path: str = "./data/chroma_db"
    collection_name: str = "documents"
    
    # BM25 設定
    bm25_k1: float = 1.5
    bm25_b: float = 0.75
    
    # Hybrid Search 設定
    rrf_k: int = 60  # Reciprocal Rank Fusion 參數
    dense_weight: float = 0.5
    sparse_weight: float = 0.5
    
    # Reranker 設定
    reranker_model: str = "BAAI/bge-reranker-base"
    reranker_top_k: int = 10
    
    # 分塊設定
    chunk_size: int = 512
    chunk_overlap: int = 50
    
    # 檢索設定
    default_top_k: int = 5
    
    @classmethod
    def from_env(cls) -> "RAGConfig":
        """從環境變數載入配置"""
        return cls(
            embedding_model=os.getenv("RAG_EMBEDDING_MODEL", cls.embedding_model),
            embedding_device=os.getenv("RAG_EMBEDDING_DEVICE", cls.embedding_device),
            vector_db_path=os.getenv("RAG_VECTOR_DB_PATH", cls.vector_db_path),
            collection_name=os.getenv("RAG_COLLECTION_NAME", cls.collection_name),
            reranker_model=os.getenv("RAG_RERANKER_MODEL", cls.reranker_model),
            default_top_k=int(os.getenv("RAG_DEFAULT_TOP_K", str(cls.default_top_k))),
        )
    
    def to_dict(self) -> dict:
        """轉為字典，方便序列化"""
        return {
            "embedding_model": self.embedding_model,
            "embedding_device": self.embedding_device,
            "embedding_batch_size": self.embedding_batch_size,
            "vector_db_path": self.vector_db_path,
            "collection_name": self.collection_name,
            "bm25_k1": self.bm25_k1,
            "bm25_b": self.bm25_b,
            "rrf_k": self.rrf_k,
            "dense_weight": self.dense_weight,
            "sparse_weight": self.sparse_weight,
            "reranker_model": self.reranker_model,
            "reranker_top_k": self.reranker_top_k,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "default_top_k": self.default_top_k,
        }
