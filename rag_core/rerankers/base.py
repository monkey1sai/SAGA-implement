"""重排序器抽象介面"""

from abc import ABC, abstractmethod
from typing import List

from ..retrievers.base import RetrievalResult


class Reranker(ABC):
    """
    重排序器抽象介面
    
    用於對初步檢索結果進行精排序，
    提高最終結果的相關性。
    """
    
    @abstractmethod
    async def rerank(
        self,
        query: str,
        results: List[RetrievalResult],
    ) -> List[RetrievalResult]:
        """
        對檢索結果重新排序
        
        Args:
            query: 原始查詢
            results: 初步檢索結果
            
        Returns:
            重新排序後的結果
        """
        ...
