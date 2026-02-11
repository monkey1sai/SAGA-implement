"""嵌入模型模組"""

from .base import EmbeddingProvider
from .bge_m3 import BGEM3Embedding

__all__ = ["EmbeddingProvider", "BGEM3Embedding"]
