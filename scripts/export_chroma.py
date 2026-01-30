import csv
import json
from pathlib import Path
from typing import Optional

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


def export_chroma_csv(persist_dir: str = "data/chroma_db", out_path: str = "data/chroma_export.csv", include_embeddings: bool = False) -> int:
    """Export Chroma collection to a CSV file.

    Returns the number of rows written.
    """
    persist_path = Path(persist_dir)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # load embeddings (same model used to build DB)
    emb = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = Chroma(persist_directory=str(persist_path), embedding_function=emb)

    col = db._collection
    include = ["metadatas", "documents"]
    if include_embeddings:
        include.append("embeddings")

    res = col.get(include=include)

    docs = res.get("documents", [])
    metas = res.get("metadatas", [])
    embs = res.get("embeddings", [])

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        headers = ["id", "source_file", "text"]
        if include_embeddings:
            headers.append("embedding_json")
        writer.writerow(headers)

        for idx in range(len(docs)):
            meta = metas[idx] if idx < len(metas) else {}
            doc = docs[idx]
            emb_vec = embs[idx] if idx < len(embs) else None

            emb_json = ""
            if include_embeddings and emb_vec is not None:
                try:
                    emb_list = emb_vec.tolist() if hasattr(emb_vec, "tolist") else list(emb_vec)
                    emb_json = json.dumps(emb_list)
                except Exception:
                    try:
                        emb_json = json.dumps(list(emb_vec))
                    except Exception:
                        emb_json = ""

            row = [idx, meta.get("source_file", ""), doc.replace("\n", " ")]
            if include_embeddings:
                row.append(emb_json)
            writer.writerow(row)

    return len(docs)


if __name__ == "__main__":
    n = export_chroma_csv()
    print(f"Exported {n} rows to data/chroma_export.csv")