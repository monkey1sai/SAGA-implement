"""
RAG 獨立 FastAPI 服務

此服務可獨立運行，提供 RESTful API 供任何專案整合。

啟動方式:
    uvicorn rag_core.server:app --host 0.0.0.0 --port 8100

API 端點:
    POST /search       - 檢索相關文件
    POST /documents    - 新增文件
    DELETE /documents  - 刪除文件
    POST /ingest       - 批次處理文件
    GET /health        - 健康檢查
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel

from .config import RAGConfig
from .embeddings import BGEM3Embedding
from .retrievers import DenseRetriever, SparseRetriever, HybridRetriever
from .rerankers import BGEReranker
from .ingest import MultimodalIngestor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 應用
app = FastAPI(
    title="RAG Core Service",
    description="可移植的 RAG 檢索服務",
    version="0.1.0",
)

# 全域配置與元件（延遲初始化）
_config: Optional[RAGConfig] = None
_retriever: Optional[HybridRetriever] = None
_ingestor: Optional[MultimodalIngestor] = None


def get_retriever() -> HybridRetriever:
    """取得或初始化 Hybrid Retriever"""
    global _config, _retriever
    
    if _retriever is None:
        _config = RAGConfig.from_env()
        
        # 初始化嵌入模型
        embedding = BGEM3Embedding(
            model_name=_config.embedding_model,
            device=_config.embedding_device,
        )
        
        # 初始化 Dense Retriever
        dense = DenseRetriever(
            embedding=embedding,
            persist_directory=_config.vector_db_path,
            collection_name=_config.collection_name,
        )
        
        # 初始化 Sparse Retriever
        sparse = SparseRetriever(
            persist_path=f"{_config.vector_db_path}/bm25_index.pkl",
            k1=_config.bm25_k1,
            b=_config.bm25_b,
        )
        
        # 初始化 Reranker
        reranker = BGEReranker(
            model_name=_config.reranker_model,
            device=_config.embedding_device,
        )
        
        # 組合成 Hybrid Retriever
        _retriever = HybridRetriever(
            dense_retriever=dense,
            sparse_retriever=sparse,
            reranker=reranker,
            rrf_k=_config.rrf_k,
            dense_weight=_config.dense_weight,
            sparse_weight=_config.sparse_weight,
        )
        
        logger.info("RAG Retriever 初始化完成")
    
    return _retriever


def get_ingestor() -> MultimodalIngestor:
    """取得或初始化文件處理器"""
    global _ingestor, _config
    
    if _ingestor is None:
        if _config is None:
            _config = RAGConfig.from_env()
        
        _ingestor = MultimodalIngestor(
            chunk_size=_config.chunk_size,
            chunk_overlap=_config.chunk_overlap,
        )
    
    return _ingestor


# ============ Request/Response Models ============

class SearchRequest(BaseModel):
    """檢索請求"""
    query: str
    top_k: int = 5
    filter_metadata: Optional[Dict[str, Any]] = None


class SearchResult(BaseModel):
    """檢索結果"""
    text: str
    score: float
    metadata: Dict[str, Any] = {}


class SearchResponse(BaseModel):
    """檢索回應"""
    results: List[SearchResult]
    query: str


class AddDocumentsRequest(BaseModel):
    """新增文件請求"""
    texts: List[str]
    metadatas: Optional[List[Dict[str, Any]]] = None


class AddDocumentsResponse(BaseModel):
    """新增文件回應"""
    ids: List[str]
    count: int


class DeleteDocumentsRequest(BaseModel):
    """刪除文件請求"""
    ids: List[str]


# ============ API Endpoints ============

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {"status": "healthy", "service": "rag-core"}


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    檢索相關文件
    
    使用 Hybrid Search (Dense + Sparse + Rerank) 找出最相關的文件片段。
    """
    try:
        retriever = get_retriever()
        results = await retriever.retrieve(
            query=request.query,
            top_k=request.top_k,
            filter_metadata=request.filter_metadata,
        )
        
        return SearchResponse(
            results=[
                SearchResult(
                    text=r.text,
                    score=r.score,
                    metadata=r.metadata,
                )
                for r in results
            ],
            query=request.query,
        )
    except Exception as e:
        logger.error(f"檢索失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents", response_model=AddDocumentsResponse)
async def add_documents(request: AddDocumentsRequest):
    """
    新增文件到索引
    
    文件會同時加入 Dense 和 Sparse 索引。
    """
    try:
        retriever = get_retriever()
        ids = await retriever.add_documents(
            texts=request.texts,
            metadatas=request.metadatas,
        )
        
        return AddDocumentsResponse(
            ids=ids,
            count=len(ids),
        )
    except Exception as e:
        logger.error(f"新增文件失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents")
async def delete_documents(request: DeleteDocumentsRequest):
    """刪除指定文件"""
    try:
        retriever = get_retriever()
        await retriever.delete_documents(request.ids)
        
        return {"deleted": len(request.ids)}
    except Exception as e:
        logger.error(f"刪除文件失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/file")
async def ingest_file(file: UploadFile = File(...)):
    """
    上傳並處理文件
    
    支援格式: PDF, DOCX, TXT, MD
    """
    try:
        # 儲存上傳的文件
        upload_dir = Path("./data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 處理文件
        ingestor = get_ingestor()
        documents = await ingestor.load(file_path)
        
        # 加入索引
        retriever = get_retriever()
        texts = [doc.text for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        ids = await retriever.add_documents(texts, metadatas)
        
        return {
            "filename": file.filename,
            "chunks": len(documents),
            "ids": ids,
        }
    except Exception as e:
        logger.error(f"處理文件失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/directory")
async def ingest_directory(directory: str, recursive: bool = True):
    """
    批次處理目錄下的所有文件
    """
    try:
        dir_path = Path(directory)
        if not dir_path.exists():
            raise HTTPException(status_code=404, detail=f"目錄不存在: {directory}")
        
        # 處理目錄
        ingestor = get_ingestor()
        documents = await ingestor.ingest_directory(dir_path, recursive)
        
        if not documents:
            return {"message": "目錄中沒有可處理的文件", "chunks": 0}
        
        # 加入索引
        retriever = get_retriever()
        texts = [doc.text for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        ids = await retriever.add_documents(texts, metadatas)
        
        return {
            "directory": directory,
            "chunks": len(documents),
            "ids": ids,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"處理目錄失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
