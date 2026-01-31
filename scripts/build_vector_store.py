import json
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from config import JSON_DIR, CHROMA_DIR
from utils import build_resume_text

# =========================
# EMBEDDINGS
# =========================
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# =========================
# MAIN
# =========================
def build_vector_store(limit: int = 400):
    files = sorted(JSON_DIR.glob("*.json"))[:limit]

    texts = []
    metadatas = []

    print(f"Building embeddings for {len(files)} CVs")

    for file in files:
        data = json.loads(file.read_text(encoding="utf-8"))
        sections = data.get("sections", {})

        text = build_resume_text(sections)
        if not text.strip():
            continue

        texts.append(text)
        metadatas.append({
            "source_file": file.name
        })

    if not texts:
        raise ValueError("No valid resume texts found.")

    db = Chroma.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
        persist_directory=str(CHROMA_DIR)
    )

    db.persist()
    print("[OK] ChromaDB built successfully")


if __name__ == "__main__":
    build_vector_store()
