"""RAG knowledge pipeline."""

from vireo_vigia.knowledge.embeddings import (
    EmbeddingProvider,
    LocalEmbeddings,
    OpenAIEmbeddings,
)
from vireo_vigia.knowledge.ingest import IngestPipeline, SemanticChunker
from vireo_vigia.knowledge.models import Chunk, Document, RetrievalResult, SearchResult
from vireo_vigia.knowledge.retriever import Retriever
from vireo_vigia.knowledge.vector_store import QdrantVectorStore

__all__ = [
    "Chunk",
    "Document",
    "EmbeddingProvider",
    "IngestPipeline",
    "LocalEmbeddings",
    "OpenAIEmbeddings",
    "QdrantVectorStore",
    "RetrievalResult",
    "Retriever",
    "SearchResult",
    "SemanticChunker",
]
