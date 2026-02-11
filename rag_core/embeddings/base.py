"""嵌入模型抽象介面"""

from abc import ABC, abstractmethod
from typing import List


class EmbeddingProvider(ABC):
    """
    嵌入模型抽象介面
    
    設計為可替換不同實作（BGE、OpenAI、Cohere 等），
    確保 RAG 模組可移植到不同專案。
    
    實作範例:
        class MyEmbedding(EmbeddingProvider):
            def embed_documents(self, texts):
                return [[0.1, 0.2, ...] for _ in texts]
            
            def embed_query(self, query):
                return [0.1, 0.2, ...]
    """
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """向量維度"""
        ...
    
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        將文件列表轉為向量
        
        Args:
            texts: 文件文字列表
            
        Returns:
            向量列表，每個向量對應一個文件
        """
        ...
    
    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """
        將查詢轉為向量
        
        Args:
            query: 查詢文字
            
        Returns:
            查詢向量
        """
        ...
