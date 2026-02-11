"""檢索器抽象介面"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class RetrievalResult:
    """
    檢索結果
    
    Attributes:
        text: 檢索到的文件內容
        score: 相關性分數（0-1，越高越相關）
        metadata: 額外元資料（來源、頁碼等）
        doc_id: 文件唯一識別碼
    """
    text: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    doc_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        """轉為字典"""
        return {
            "text": self.text,
            "score": self.score,
            "metadata": self.metadata,
            "doc_id": self.doc_id,
        }


class Retriever(ABC):
    """
    檢索器抽象介面
    
    所有檢索器（Dense、Sparse、Hybrid）都實作此介面，
    確保可互換使用。
    """
    
    @abstractmethod
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """
        根據查詢檢索相關文件
        
        Args:
            query: 查詢文字
            top_k: 返回前 K 個結果
            filter_metadata: 可選的元資料過濾條件
            
        Returns:
            檢索結果列表，按相關性分數降序排列
        """
        ...
    
    @abstractmethod
    async def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """
        新增文件到索引
        
        Args:
            texts: 文件文字列表
            metadatas: 對應的元資料列表
            ids: 可選的文件 ID 列表
            
        Returns:
            新增的文件 ID 列表
        """
        ...
    
    async def delete_documents(self, ids: List[str]) -> None:
        """
        刪除指定文件
        
        Args:
            ids: 要刪除的文件 ID 列表
        """
        raise NotImplementedError("此檢索器不支援刪除操作")
