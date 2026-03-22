from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from RAG_service.vector_store import vector_store
from langchain_core.documents import Document
from werkzeug.utils import secure_filename
from fastapi import UploadFile
import hashlib 
import shutil
import json
import os

class Chunker:
    
    def __init__(self, chunk_size=500, chunk_overlap=50):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap)

    def upload(self, source_file: UploadFile):

        filename = secure_filename(source_file.filename)
        destination = os.path.join(self.upload_dir, filename)

        with open(destination, "wb") as out_file:
            shutil.copyfileobj(source_file.file, out_file)
      
        loader = PyPDFLoader(destination)
        pages = loader.load()

        page_docs = []
        for page in pages:
            text = page["text"]

            doc = Document(
                page_content=text,
                metadata={
                    "source": destination,
                    "page_number": page["page_number"],
                }
            )
            page_docs.append(doc)

        # Split pages into overlapping chunks
        chunk_docs = self.splitter.split_documents(page_docs)

        # Assign a hash per chunk (for versioning + dedupe)
        for d in chunk_docs:
            d.metadata["hash"] = hash_text(d.page_content)

        vector_store.add_documents(chunk_docs)
        vector_store.persist()

        return {
            "file": destination,
            "pages": len(pages),
            "chunks": len(chunk_docs)
            }

def hash_text(text: str) -> str:
    """Generate SHA-256 hash of text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()