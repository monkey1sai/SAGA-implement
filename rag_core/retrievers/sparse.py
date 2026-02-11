"""Sparse 稀疏檢索器 (BM25)"""

from typing import List, Dict, Any, Optional
import uuid
import logging
import pickle
from pathlib import Path

from .base import Retriever, RetrievalResult

logger = logging.getLogger(__name__)


class SparseRetriever(Retriever):
    """
    Sparse 稀疏檢索器 (BM25)
    
    使用 BM25 演算法進行關鍵詞檢索，支援：
    - 中文斷詞 (jieba)
    - 持久化存儲
    - 增量更新
    
    Args:
        persist_path: 索引持久化路徑
        k1: BM25 k1 參數
        b: BM25 b 參數
    """
    
    def __init__(
        self,
        persist_path: str = "./data/bm25_index.pkl",
        k1: float = 1.5,
        b: float = 0.75,
    ):
        self.persist_path = Path(persist_path)
        self.k1 = k1
        self.b = b
        
        self._bm25 = None
        self._documents: List[str] = []
        self._metadatas: List[Dict[str, Any]] = []
        self._ids: List[str] = []
        self._tokenized_corpus: List[List[str]] = []
        
        self._load_index()
    
    def _tokenize(self, text: str) -> List[str]:
        """中文斷詞"""
        try:
            import jieba
            return list(jieba.cut(text))
        except ImportError:
            # 退化為字元分割
            logger.warning("jieba 未安裝，使用字元分割")
            return list(text)
    
    def _build_bm25(self):
        """建立 BM25 索引"""
        if not self._tokenized_corpus:
            self._bm25 = None
            return
        
        try:
            from rank_bm25 import BM25Okapi
            self._bm25 = BM25Okapi(
                self._tokenized_corpus,
                k1=self.k1,
                b=self.b,
            )
        except ImportError:
            raise ImportError("請安裝 rank_bm25: pip install rank-bm25")
    
    def _load_index(self):
        """從檔案載入索引"""
        if self.persist_path.exists():
            try:
                with open(self.persist_path, "rb") as f:
                    data = pickle.load(f)
                self._documents = data.get("documents", [])
                self._metadatas = data.get("metadatas", [])
                self._ids = data.get("ids", [])
                self._tokenized_corpus = data.get("tokenized_corpus", [])
                self._build_bm25()
                logger.info(f"已載入 BM25 索引: {len(self._documents)} 個文件")
            except Exception as e:
                logger.warning(f"載入 BM25 索引失敗: {e}")
    
    def _save_index(self):
        """儲存索引到檔案"""
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "documents": self._documents,
            "metadatas": self._metadatas,
            "ids": self._ids,
            "tokenized_corpus": self._tokenized_corpus,
        }
        with open(self.persist_path, "wb") as f:
            pickle.dump(data, f)
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """BM25 關鍵詞檢索"""
        if self._bm25 is None or not self._documents:
            return []
        
        # 斷詞查詢
        tokenized_query = self._tokenize(query)
        
        # 計算 BM25 分數
        scores = self._bm25.get_scores(tokenized_query)
        
        # 排序並取 top_k
        scored_indices = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True,
        )[:top_k]
        
        # 轉換結果
        results = []
        for idx, score in scored_indices:
            if score <= 0:
                continue
            
            metadata = self._metadatas[idx] if idx < len(self._metadatas) else {}
            
            # 元資料過濾
            if filter_metadata:
                if not all(metadata.get(k) == v for k, v in filter_metadata.items()):
                    continue
            
            results.append(RetrievalResult(
                text=self._documents[idx],
                score=float(score),
                metadata=metadata,
                doc_id=self._ids[idx] if idx < len(self._ids) else None,
            ))
        
        return results
    
    async def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """新增文件到 BM25 索引"""
        if not texts:
            return []
        
        # 產生 ID
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
        
        # 準備元資料
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        # 斷詞並新增
        for text, metadata, doc_id in zip(texts, metadatas, ids):
            self._documents.append(text)
            self._metadatas.append(metadata)
            self._ids.append(doc_id)
            self._tokenized_corpus.append(self._tokenize(text))
        
        # 重建索引
        self._build_bm25()
        self._save_index()
        
        logger.info(f"已新增 {len(texts)} 個文件到 BM25 索引")
        return ids
    
    async def delete_documents(self, ids: List[str]) -> None:
        """刪除指定文件"""
        ids_set = set(ids)
        indices_to_keep = [
            i for i, doc_id in enumerate(self._ids)
            if doc_id not in ids_set
        ]
        
        self._documents = [self._documents[i] for i in indices_to_keep]
        self._metadatas = [self._metadatas[i] for i in indices_to_keep]
        self._ids = [self._ids[i] for i in indices_to_keep]
        self._tokenized_corpus = [self._tokenized_corpus[i] for i in indices_to_keep]
        
        self._build_bm25()
        self._save_index()
        
        logger.info(f"已刪除 {len(ids)} 個文件")
    
    def get_document_count(self) -> int:
        """取得文件總數"""
        return len(self._documents)
