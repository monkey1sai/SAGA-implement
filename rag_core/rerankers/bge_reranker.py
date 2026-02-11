"""BGE Reranker 實作"""

from typing import List, Optional
import logging

from .base import Reranker
from ..retrievers.base import RetrievalResult

logger = logging.getLogger(__name__)


class BGEReranker(Reranker):
    """
    BAAI/bge-reranker-base 重排序器
    
    使用交叉編碼器對 query-document 對進行評分，
    比向量相似度更準確但計算成本更高。
    
    Args:
        model_name: 模型名稱
        device: 運算裝置
        use_fp16: 是否使用 FP16
    """
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-base",
        device: str = "cuda",
        use_fp16: bool = True,
    ):
        self.model_name = model_name
        self.device = device
        self.use_fp16 = use_fp16
        self._reranker = None
    
    def _ensure_model(self):
        """延遲載入模型"""
        if self._reranker is None:
            try:
                from FlagEmbedding import FlagReranker
                
                logger.info(f"載入 Reranker 模型: {self.model_name}")
                self._reranker = FlagReranker(
                    self.model_name,
                    use_fp16=self.use_fp16,
                    device=self.device,
                )
                logger.info("Reranker 模型載入完成")
            except ImportError:
                raise ImportError(
                    "請安裝 FlagEmbedding: pip install FlagEmbedding"
                )
    
    async def rerank(
        self,
        query: str,
        results: List[RetrievalResult],
    ) -> List[RetrievalResult]:
        """使用 BGE Reranker 重新排序"""
        if not results:
            return []
        
        self._ensure_model()
        
        # 準備 query-document 對
        pairs = [[query, r.text] for r in results]
        
        # 計算 rerank 分數
        scores = self._reranker.compute_score(pairs, normalize=True)
        
        # 確保 scores 是列表
        if not isinstance(scores, list):
            scores = [scores]
        
        # 更新分數並排序
        reranked = []
        for result, score in zip(results, scores):
            reranked.append(RetrievalResult(
                text=result.text,
                score=float(score),
                metadata=result.metadata,
                doc_id=result.doc_id,
            ))
        
        # 按分數降序排列
        reranked.sort(key=lambda x: x.score, reverse=True)
        
        return reranked
