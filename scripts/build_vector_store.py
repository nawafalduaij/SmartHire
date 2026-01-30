from pathlib import Path
import json
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# =========================
# PATHS
# =========================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = PROJECT_ROOT / "data" / "processed" / "resumes_sectioned_json"
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma_db"

CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# ENV
# =========================
# HuggingFace embeddings don't require API keys
load_dotenv(PROJECT_ROOT / ".env")

# =========================
# EMBEDDINGS
# =========================
# Using HuggingFace embeddings (local, no API calls needed)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# =========================
# HELPERS
# =========================
def resume_to_text(sections: dict) -> str:
    parts = []

    if sections.get("summary"):
        parts.append(sections["summary"])

    for exp in sections.get("experience", []):
        parts.append(
            f"{exp.get('title', '')} at {exp.get('company', '')}. "
            + " ".join(exp.get("responsibilities", []))
        )

    for edu in sections.get("education", []):
        parts.append(
            f"{edu.get('degree', '')} in {edu.get('field', '')} from {edu.get('institution', '')}"
        )

    parts.extend(sections.get("skills", []))

    return "\n".join([p for p in parts if p])


# =========================
# MAIN
# =========================
def build_vector_store(limit: int = 400):
    files = sorted(INPUT_DIR.glob("*.json"))[:limit]

    texts = []
    metadatas = []

    print(f"Building embeddings for {len(files)} CVs")

    for file in files:
        data = json.loads(file.read_text(encoding="utf-8"))
        sections = data.get("sections", {})

        text = resume_to_text(sections)
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
