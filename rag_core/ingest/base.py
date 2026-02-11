"""文件載入器抽象介面"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path


@dataclass
class Document:
    """
    文件資料結構
    
    Attributes:
        text: 文件內容文字
        metadata: 元資料（來源、頁碼、類型等）
        chunk_type: 分塊類型（semantic/slide/table/image）
    """
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunk_type: str = "text"
    
    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "metadata": self.metadata,
            "chunk_type": self.chunk_type,
        }


class DocumentLoader(ABC):
    """
    文件載入器抽象介面
    
    所有文件格式載入器都實作此介面，
    確保可統一處理不同格式。
    """
    
    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """支援的檔案副檔名"""
        ...
    
    @abstractmethod
    async def load(self, file_path: Path) -> List[Document]:
        """
        載入並處理文件
        
        Args:
            file_path: 文件路徑
            
        Returns:
            處理後的文件片段列表
        """
        ...
    
    def can_load(self, file_path: Path) -> bool:
        """檢查是否支援此文件格式"""
        suffix = file_path.suffix.lower()
        return suffix in self.supported_extensions
