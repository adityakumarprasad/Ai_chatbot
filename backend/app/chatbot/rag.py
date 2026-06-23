import os
import tempfile
from typing import Dict, Any, Optional
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

# In-memory stores mapping thread_id (str) to vector store indices, retrievers, and metadata
_THREAD_VECTOR_STORES: Dict[str, FAISS] = {}
_THREAD_RETRIEVERS: Dict[str, Any] = {}
_THREAD_METADATA: Dict[str, dict] = {}

def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Return the Google Generative AI embeddings helper."""
    return GoogleGenerativeAIEmbeddings(model="gemini-embedding-2-preview")

def get_retriever(thread_id: Optional[str]):
    """Retrieve the unified document retriever for the active thread."""
    if thread_id and str(thread_id) in _THREAD_RETRIEVERS:
        return _THREAD_RETRIEVERS[str(thread_id)]
    return None

def thread_has_document(thread_id: str) -> bool:
    """Check if the thread has at least one uploaded document."""
    return str(thread_id) in _THREAD_VECTOR_STORES

def thread_document_metadata(thread_id: str) -> dict:
    """Get metadata about all files uploaded to the specified thread."""
    return _THREAD_METADATA.get(str(thread_id), {})

def ingest_pdf(file_bytes: bytes, thread_id: str, filename: Optional[str] = None) -> dict:
    """
    Parse the PDF document, split it into chunks, and index it.
    If the thread already has a vector database, the chunks are appended to it.
    Otherwise, a new database is initialized.
    """
    if not file_bytes:
        raise ValueError("No file content received.")

    t_id = str(thread_id)

    # Write binary bytes to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(file_bytes)
        temp_path = temp_file.name

    try:
        # Load PDF pages
        loader = PyPDFLoader(temp_path)
        docs = loader.load()

        # Split text into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = splitter.split_documents(docs)

        embeddings = get_embeddings()
        file_name = filename or os.path.basename(temp_path)
        num_docs = len(docs)
        num_chunks = len(chunks)

        if t_id not in _THREAD_VECTOR_STORES:
            # Initialize FAISS vector database for this thread
            vector_store = FAISS.from_documents(chunks, embeddings)
            _THREAD_VECTOR_STORES[t_id] = vector_store
            _THREAD_RETRIEVERS[t_id] = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 4}
            )
            _THREAD_METADATA[t_id] = {
                "files": [
                    {"filename": file_name, "documents": num_docs, "chunks": num_chunks}
                ],
                "total_documents": num_docs,
                "total_chunks": num_chunks
            }
        else:
            # Append the new document's chunks to the existing database index
            vector_store = _THREAD_VECTOR_STORES[t_id]
            vector_store.add_documents(chunks)
            
            # Update combined metadata
            metadata = _THREAD_METADATA[t_id]
            metadata["files"].append(
                {"filename": file_name, "documents": num_docs, "chunks": num_chunks}
            )
            metadata["total_documents"] += num_docs
            metadata["total_chunks"] += num_chunks

        return _THREAD_METADATA[t_id]
        
    finally:
        # Clean up temporary file
        try:
            os.remove(temp_path)
        except OSError:
            pass
