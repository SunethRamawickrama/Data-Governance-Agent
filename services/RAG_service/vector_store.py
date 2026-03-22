from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceBgeEmbeddings


class VectorStore:
    """Wrapper for vector database operations."""
    
    def __init__(self, persist_directory: str = "vector_store"):
        self.embeddings = HuggingFaceBgeEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.store = Chroma(
            embedding_function=self.embeddings,
            persist_directory=persist_directory
        )

    def add_documents(self, docs, batch_size: int = 32):
        """
        Add documents in small batches to control load.
        """
        for i in range(0, len(docs), batch_size):
            batch = docs[i:i + batch_size]
            self.store.add_documents(batch)

    def persist(self):
        """Persist vector store to disk."""
        self.store.persist()

    def search(self, query: str, k: int = 5):
        """Search for similar documents."""
        return self.store.similarity_search(query, k=k)

vector_store = VectorStore()
