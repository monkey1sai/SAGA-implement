"""Dense 向量檢索器 (ChromaDB)"""

from typing import List, Dict, Any, Optional
import uuid
import logging

from .base import Retriever, RetrievalResult
from ..embeddings.base import EmbeddingProvider

logger = logging.getLogger(__name__)


class DenseRetriever(Retriever):
    """
    Dense 向量檢索器
    
    使用 ChromaDB 作為向量資料庫，支援：
    - 高效向量相似度搜尋
    - 元資料過濾
    - 持久化存儲
    
    Args:
        embedding: 嵌入模型提供者
        persist_directory: 持久化目錄路徑
        collection_name: 集合名稱
    """
    
    def __init__(
        self,
        embedding: EmbeddingProvider,
        persist_directory: str = "./data/chroma_db",
        collection_name: str = "documents",
    ):
        self.embedding = embedding
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self._client = None
        self._collection = None
    
    def _ensure_collection(self):
        """延遲初始化 ChromaDB"""
        if self._collection is None:
            try:
                import chromadb
                from chromadb.config import Settings
                
                logger.info(f"初始化 ChromaDB: {self.persist_directory}")
                self._client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=Settings(anonymized_telemetry=False),
                )
                self._collection = self._client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
                logger.info(f"ChromaDB 集合 '{self.collection_name}' 已就緒")
            except ImportError:
                raise ImportError("請安裝 chromadb: pip install chromadb")
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """向量相似度檢索"""
        self._ensure_collection()
        
        # 取得查詢向量
        query_embedding = self.embedding.embed_query(query)
        
        # 執行檢索
        where_filter = filter_metadata if filter_metadata else None
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
        
        # 轉換結果
        retrieval_results = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                # ChromaDB 回傳的是距離，轉換為相似度分數
                distance = results["distances"][0][i] if results["distances"] else 0
                score = 1 - distance  # cosine distance to similarity
                
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                doc_id = results["ids"][0][i] if results["ids"] else None
                
                retrieval_results.append(RetrievalResult(
                    text=doc,
                    score=score,
                    metadata=metadata,
                    doc_id=doc_id,
                ))
        
        return retrieval_results
    
    async def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """新增文件到向量資料庫"""
        self._ensure_collection()
        
        if not texts:
            return []
        
        # 產生 ID
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
        
        # 產生嵌入向量
        embeddings = self.embedding.embed_documents(texts)
        
        # 準備元資料
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        # 新增到集合
        self._collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )
        
        logger.info(f"已新增 {len(texts)} 個文件到向量資料庫")
        return ids
    
    async def delete_documents(self, ids: List[str]) -> None:
        """刪除指定文件"""
        self._ensure_collection()
        self._collection.delete(ids=ids)
        logger.info(f"已刪除 {len(ids)} 個文件")
    
    def get_document_count(self) -> int:
        """取得文件總數"""
        self._ensure_collection()
        return self._collection.count()
