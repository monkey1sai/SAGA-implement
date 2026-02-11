"""Hybrid 混合檢索器 (Dense + Sparse + RRF + Rerank)"""

from typing import List, Dict, Any, Optional
import logging
from collections import defaultdict

from .base import Retriever, RetrievalResult

logger = logging.getLogger(__name__)


class HybridRetriever(Retriever):
    """
    Hybrid 混合檢索器
    
    結合 Dense (向量) 和 Sparse (BM25) 檢索，
    使用 Reciprocal Rank Fusion (RRF) 融合結果，
    可選配 Reranker 進行精排序。
    
    架構:
        Query
          ├─→ Dense Search (ChromaDB)
          └─→ Sparse Search (BM25)
                 ↓
          Reciprocal Rank Fusion (RRF)
                 ↓
          Reranking (optional)
                 ↓
          Top-K Results
    
    Args:
        dense_retriever: Dense 向量檢索器
        sparse_retriever: Sparse 稀疏檢索器
        reranker: 可選的重排序器
        rrf_k: RRF 參數 (預設 60)
        dense_weight: Dense 結果權重
        sparse_weight: Sparse 結果權重
    """
    
    def __init__(
        self,
        dense_retriever: Retriever,
        sparse_retriever: Retriever,
        reranker: Optional["Reranker"] = None,
        rrf_k: int = 60,
        dense_weight: float = 0.5,
        sparse_weight: float = 0.5,
    ):
        self.dense_retriever = dense_retriever
        self.sparse_retriever = sparse_retriever
        self.reranker = reranker
        self.rrf_k = rrf_k
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
    
    def _reciprocal_rank_fusion(
        self,
        results_list: List[List[RetrievalResult]],
        weights: List[float],
    ) -> List[RetrievalResult]:
        """
        Reciprocal Rank Fusion (RRF)
        
        RRF 公式: score = sum(weight / (k + rank))
        其中 k 是平滑參數，rank 是結果在各列表中的排名
        """
        # 收集所有唯一文件及其 RRF 分數
        doc_scores: Dict[str, float] = defaultdict(float)
        doc_texts: Dict[str, str] = {}
        doc_metadata: Dict[str, Dict] = {}
        
        for results, weight in zip(results_list, weights):
            for rank, result in enumerate(results, start=1):
                # 用文字當作唯一識別（也可以用 doc_id）
                doc_key = result.text[:200]  # 取前 200 字作為 key
                
                # RRF 分數累加
                rrf_score = weight / (self.rrf_k + rank)
                doc_scores[doc_key] += rrf_score
                
                # 保留文件資訊
                if doc_key not in doc_texts:
                    doc_texts[doc_key] = result.text
                    doc_metadata[doc_key] = result.metadata
        
        # 按 RRF 分數排序
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        
        # 轉換為 RetrievalResult
        return [
            RetrievalResult(
                text=doc_texts[doc_key],
                score=score,
                metadata=doc_metadata[doc_key],
            )
            for doc_key, score in sorted_docs
        ]
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """
        執行 Hybrid Search
        
        流程:
        1. 並行執行 Dense 和 Sparse 檢索
        2. 使用 RRF 融合結果
        3. 可選: 使用 Reranker 精排序
        4. 返回 top_k 結果
        """
        # 擴大初始檢索數量以供 RRF 融合
        initial_k = min(top_k * 3, 50)
        
        # 並行檢索
        import asyncio
        dense_task = self.dense_retriever.retrieve(query, initial_k, filter_metadata)
        sparse_task = self.sparse_retriever.retrieve(query, initial_k, filter_metadata)
        
        dense_results, sparse_results = await asyncio.gather(dense_task, sparse_task)
        
        logger.debug(f"Dense 結果: {len(dense_results)}, Sparse 結果: {len(sparse_results)}")
        
        # RRF 融合
        fused_results = self._reciprocal_rank_fusion(
            [dense_results, sparse_results],
            [self.dense_weight, self.sparse_weight],
        )
        
        # Rerank（如果有）
        if self.reranker and fused_results:
            rerank_k = min(len(fused_results), top_k * 2)
            fused_results = await self.reranker.rerank(
                query,
                fused_results[:rerank_k],
            )
        
        return fused_results[:top_k]
    
    async def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """同時新增文件到 Dense 和 Sparse 索引"""
        import asyncio
        
        # 並行新增
        dense_task = self.dense_retriever.add_documents(texts, metadatas, ids)
        sparse_task = self.sparse_retriever.add_documents(texts, metadatas, ids)
        
        dense_ids, sparse_ids = await asyncio.gather(dense_task, sparse_task)
        
        logger.info(f"已新增 {len(texts)} 個文件到 Hybrid 索引")
        return dense_ids
    
    async def delete_documents(self, ids: List[str]) -> None:
        """同時從 Dense 和 Sparse 索引刪除文件"""
        import asyncio
        
        await asyncio.gather(
            self.dense_retriever.delete_documents(ids),
            self.sparse_retriever.delete_documents(ids),
        )
        
        logger.info(f"已從 Hybrid 索引刪除 {len(ids)} 個文件")
