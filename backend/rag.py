import os
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader
from dotenv import load_dotenv

load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, "data")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

# ── ChromaDB setup ────────────────────────────────────────────────
def get_collection():
    """Get or create the ChromaDB collection."""
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    collection = client.get_or_create_collection(
        name="air_quality_docs",
        embedding_function=ef
    )
    return collection


def load_pdfs():
    """
    Load all PDFs from the data folder into ChromaDB.
    Splits each PDF into chunks and stores with metadata.
    """
    collection = get_collection()

    # Check if already loaded
    if collection.count() > 0:
        print(f"ChromaDB already has {collection.count()} chunks loaded.")
        return collection

    pdf_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".pdf")]

    if not pdf_files:
        print("No PDFs found in data folder.")
        return collection

    print(f"Loading {len(pdf_files)} PDF(s) into ChromaDB...")

    all_chunks = []
    all_ids    = []
    all_metas  = []

    for pdf_file in pdf_files:
        path   = os.path.join(DATA_DIR, pdf_file)
        reader = PdfReader(path)

        print(f"  Processing {pdf_file} ({len(reader.pages)} pages)...")

        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if not text or len(text.strip()) < 50:
                continue

            # Split page into chunks of ~500 characters
            chunks = split_text(text, chunk_size=500, overlap=50)

            for i, chunk in enumerate(chunks):
                chunk_id = f"{pdf_file}_page{page_num}_chunk{i}"
                all_chunks.append(chunk)
                all_ids.append(chunk_id)
                all_metas.append({
                    "source":   pdf_file,
                    "page":     page_num + 1,
                    "chunk":    i,
                })

    if all_chunks:
        # Add in batches of 100
        batch_size = 100
        for i in range(0, len(all_chunks), batch_size):
            collection.add(
                documents=all_ids[i:i+batch_size],
                ids=all_ids[i:i+batch_size],
                metadatas=all_metas[i:i+batch_size],
            )
            # Re-add with actual text
            collection.upsert(
                documents=all_chunks[i:i+batch_size],
                ids=all_ids[i:i+batch_size],
                metadatas=all_metas[i:i+batch_size],
            )

        print(f"Loaded {len(all_chunks)} chunks into ChromaDB.")

    return collection


def split_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """Split text into overlapping chunks."""
    chunks = []
    start  = 0
    text   = text.strip()

    while start < len(text):
        end   = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap

    return chunks


def search_documents(query: str, n_results: int = 4) -> str:
    """
    Search the RAG knowledge base for relevant information.
    Returns formatted results with source citations.
    """
    collection = get_collection()

    if collection.count() == 0:
        return "Knowledge base is empty. Please load PDF documents first."

    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count())
    )

    if not results["documents"] or not results["documents"][0]:
        return "No relevant information found in the knowledge base."

    output = []
    output.append(f"=== Knowledge Base Results for: '{query}' ===\n")

    for i, (doc, meta) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0]
    )):
        source = meta.get("source", "Unknown")
        page   = meta.get("page", "?")
        output.append(f"[Source {i+1}: {source}, Page {page}]")
        output.append(doc.strip())
        output.append("")

    return "\n".join(output)


def get_rag_status() -> dict:
    """Return status of the RAG knowledge base."""
    collection = get_collection()
    pdf_files  = [f for f in os.listdir(DATA_DIR) if f.endswith(".pdf")]
    return {
        "chunks_loaded": collection.count(),
        "pdfs_in_folder": len(pdf_files),
        "pdf_files": pdf_files,
        "status": "ready" if collection.count() > 0 else "empty"
    }