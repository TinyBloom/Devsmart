"""
RAG Service - 轻量级向量检索服务
基于 ChromaDB 实现三层记忆架构的检索功能

注意事项：
1. ChromaDB Python 客户端是同步的，所有方法都使用 asyncio.to_thread() 包装
2. 默认使用 all-MiniLM-L6-v2 嵌入模型，首次使用会自动下载（约 80MB）
3. 当 RAG 服务不可用时，会自动降级为空结果，由调用方处理回退逻辑
4. chromadb 采用延迟导入，确保模块加载时不会因为缺少依赖而失败
"""

import asyncio
import uuid
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

_chromadb = None
_Settings = None


def _import_chromadb():
    """延迟导入 chromadb，避免模块加载时失败"""
    global _chromadb, _Settings
    if _chromadb is None:
        try:
            import chromadb
            from chromadb.config import Settings
            _chromadb = chromadb
            _Settings = Settings
            return True
        except ImportError:
            logger.warning("[RAG] chromadb 未安装，RAG 功能将不可用")
            return False
    return True


class RAGService:
    """RAG 向量检索服务"""

    def __init__(self):
        self._client = None
        self._long_term_collection = None
        self._medium_term_collection = None

    async def _get_client(self):
        """
        延迟初始化 ChromaDB 客户端（首次使用时初始化）
        
        Returns:
            ChromaDB PersistentClient（未安装 chromadb 时返回 None）
        """
        if not _import_chromadb():
            raise ImportError("chromadb 未安装")
        
        if self._client is None:
            try:
                self._client = _chromadb.PersistentClient(
                    path="./rag_db",
                    settings=_Settings(allow_reset=True)
                )
                self._long_term_collection = self._client.get_or_create_collection(
                    name="long_term_memory",
                    metadata={"description": "项目长期记忆库 - 存储模板数据、PRD、技术文档等"}
                )
                self._medium_term_collection = self._client.get_or_create_collection(
                    name="medium_term_memory",
                    metadata={"description": "项目中期记忆库 - 存储对话摘要、关键决策点"}
                )
            except Exception as e:
                logger.error(f"[RAG 初始化失败] {type(e).__name__}: {str(e)}")
                raise
        return self._client

    def _enforce_project_id(self, project_id: str, metadata: Optional[Dict]) -> Dict:
        """
        强制在 metadata 中包含 project_id
        
        Args:
            project_id: 项目 ID
            metadata: 原始元数据
            
        Returns:
            确保包含 project_id 的元数据
            
        Raises:
            ValueError: 如果 project_id 为空
        """
        if not project_id:
            raise ValueError("project_id 不能为空")
        
        result = metadata.copy() if metadata else {}
        result["project_id"] = project_id
        return result

    async def add_long_term_document(
        self,
        project_id: str,
        content: str,
        metadata: Optional[Dict] = None,
        timeout: int = 30
    ) -> str:
        """
        向长期记忆库添加文档

        Args:
            project_id: 项目 ID
            content: 文档内容
            metadata: 文档元数据（如 type, phase 等）
            timeout: 超时时间（秒）

        Returns:
            文档 ID（失败时返回空字符串）
        """
        try:
            await self._get_client()
            
            safe_metadata = self._enforce_project_id(project_id, metadata)
            
            doc_id = f"{project_id}_{uuid.uuid4()}"
            await asyncio.wait_for(
                asyncio.to_thread(
                    self._long_term_collection.add,
                    documents=[content],
                    metadatas=[safe_metadata],
                    ids=[doc_id]
                ),
                timeout=timeout
            )
            logger.info(f"[RAG 添加长期文档成功] project_id={project_id}, doc_id={doc_id}")
            return doc_id
        except asyncio.TimeoutError:
            logger.warning(f"[RAG 添加长期文档超时] project_id={project_id}, timeout={timeout}s")
            return ""
        except Exception as e:
            logger.error(f"[RAG 添加长期文档失败] project_id={project_id}, error={str(e)}")
            return ""

    async def add_medium_term_document(
        self,
        project_id: str,
        content: str,
        metadata: Optional[Dict] = None,
        timeout: int = 30
    ) -> str:
        """
        向中期记忆库添加文档

        Args:
            project_id: 项目 ID
            content: 文档内容（如对话摘要）
            metadata: 文档元数据
            timeout: 超时时间（秒）

        Returns:
            文档 ID（失败时返回空字符串）
        """
        try:
            await self._get_client()
            
            safe_metadata = self._enforce_project_id(project_id, metadata)
            
            doc_id = f"{project_id}_{uuid.uuid4()}"
            await asyncio.wait_for(
                asyncio.to_thread(
                    self._medium_term_collection.add,
                    documents=[content],
                    metadatas=[safe_metadata],
                    ids=[doc_id]
                ),
                timeout=timeout
            )
            logger.info(f"[RAG 添加中期文档成功] project_id={project_id}, doc_id={doc_id}")
            return doc_id
        except asyncio.TimeoutError:
            logger.warning(f"[RAG 添加中期文档超时] project_id={project_id}, timeout={timeout}s")
            return ""
        except Exception as e:
            logger.error(f"[RAG 添加中期文档失败] project_id={project_id}, error={str(e)}")
            return ""

    async def query_long_term(
        self,
        project_id: str,
        query: str,
        top_k: int = 3
    ) -> List[Dict]:
        """
        检索长期记忆库

        Args:
            project_id: 项目 ID
            query: 查询文本
            top_k: 返回数量

        Returns:
            检索结果列表（RAG 服务不可用时返回空列表）
        """
        try:
            await self._get_client()
            
            results = await asyncio.to_thread(
                self._long_term_collection.query,
                query_texts=[query],
                n_results=top_k,
                where={"project_id": project_id}
            )
            formatted = self._format_results(results)
            logger.debug(f"[RAG 检索长期记忆] project_id={project_id}, query={query[:20]}..., results={len(formatted)}")
            return formatted
        except Exception as e:
            logger.warning(f"[RAG 检索长期记忆失败] project_id={project_id}, error={str(e)}")
            return []

    async def query_medium_term(
        self,
        project_id: str,
        query: str,
        top_k: int = 2
    ) -> List[Dict]:
        """
        检索中期记忆库

        Args:
            project_id: 项目 ID
            query: 查询文本
            top_k: 返回数量

        Returns:
            检索结果列表（RAG 服务不可用时返回空列表）
        """
        try:
            await self._get_client()
            
            results = await asyncio.to_thread(
                self._medium_term_collection.query,
                query_texts=[query],
                n_results=top_k,
                where={"project_id": project_id}
            )
            formatted = self._format_results(results)
            logger.debug(f"[RAG 检索中期记忆] project_id={project_id}, query={query[:20]}..., results={len(formatted)}")
            return formatted
        except Exception as e:
            logger.warning(f"[RAG 检索中期记忆失败] project_id={project_id}, error={str(e)}")
            return []

    async def delete_project_documents(self, project_id: str):
        """
        删除项目的所有记忆文档

        Args:
            project_id: 项目 ID
        """
        try:
            await self._get_client()
            
            await asyncio.to_thread(
                self._long_term_collection.delete,
                where={"project_id": project_id}
            )
            await asyncio.to_thread(
                self._medium_term_collection.delete,
                where={"project_id": project_id}
            )
            logger.info(f"[RAG 删除项目文档成功] project_id={project_id}")
        except Exception as e:
            logger.error(f"[RAG 删除项目文档失败] project_id={project_id}, error={str(e)}")

    def _format_results(self, results: Dict) -> List[Dict]:
        """
        格式化检索结果

        Args:
            results: ChromaDB 查询结果

        Returns:
            格式化后的结果列表
        """
        formatted = []
        if results.get("documents") and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                formatted.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "distance": results["distances"][0][i] if results.get("distances") else 0
                })
        return formatted

    async def get_collection_stats(self, collection_type: str = "long_term") -> Dict:
        """
        获取集合统计信息

        Args:
            collection_type: 集合类型（long_term / medium_term）

        Returns:
            统计信息字典
        """
        try:
            await self._get_client()
            
            collection = self._long_term_collection if collection_type == "long_term" else self._medium_term_collection
            stats = await asyncio.to_thread(collection.count)
            
            return {
                "collection": collection_type,
                "document_count": stats,
                "status": "healthy"
            }
        except Exception as e:
            return {
                "collection": collection_type,
                "document_count": 0,
                "status": "unhealthy",
                "error": str(e)
            }