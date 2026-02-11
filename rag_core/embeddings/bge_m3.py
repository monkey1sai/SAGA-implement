"""BGE-M3 嵌入模型實作"""

from typing import List, Optional
import logging

from .base import EmbeddingProvider

logger = logging.getLogger(__name__)


class BGEM3Embedding(EmbeddingProvider):
    """
    BAAI/bge-m3 嵌入模型
    
    特點：
    - 支援 8192 tokens 長文本
    - 多語言支援（含中文）
    - Dense + Sparse 雙重表示
    
    Args:
        model_name: 模型名稱，預設 "BAAI/bge-m3"
        device: 運算裝置，"cuda" 或 "cpu"
        use_fp16: 是否使用 FP16 加速
    """
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        device: str = "cuda",
        use_fp16: bool = True,
    ):
        self.model_name = model_name
        self.device = device
        self.use_fp16 = use_fp16
        self._model = None
        self._dimension = 1024  # BGE-M3 預設維度
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    def _ensure_model(self):
        """延遲載入模型"""
        if self._model is None:
            try:
                from FlagEmbedding import BGEM3FlagModel
                
                logger.info(f"載入嵌入模型: {self.model_name}")
                self._model = BGEM3FlagModel(
                    self.model_name,
                    use_fp16=self.use_fp16,
                    device=self.device,
                )
                logger.info("嵌入模型載入完成")
            except ImportError:
                raise ImportError(
                    "請安裝 FlagEmbedding: pip install FlagEmbedding"
                )
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """將文件列表轉為向量"""
        if not texts:
            return []
        
        self._ensure_model()
        
        # BGE-M3 回傳 dense_vecs
        embeddings = self._model.encode(
            texts,
            batch_size=32,
            max_length=8192,
        )["dense_vecs"]
        
        return embeddings.tolist()
    
    def embed_query(self, query: str) -> List[float]:
        """將查詢轉為向量"""
        self._ensure_model()
        
        embeddings = self._model.encode(
            [query],
            batch_size=1,
            max_length=8192,
        )["dense_vecs"]
        
        return embeddings[0].tolist()
    
    def embed_with_sparse(self, texts: List[str]) -> dict:
        """
        同時取得 Dense 和 Sparse 表示
        
        Returns:
            {"dense_vecs": [...], "lexical_weights": [...]}
        """
        self._ensure_model()
        
        return self._model.encode(
            texts,
            batch_size=32,
            max_length=8192,
            return_dense=True,
            return_sparse=True,
        )
