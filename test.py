import csv, json
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

emb = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db = Chroma(persist_directory="data/chroma_db", embedding_function=emb)

col = db._collection
# remove 'ids' — only include allowed keys
res = col.get(include=['metadatas', 'documents', 'embeddings'])

with open('data/chroma_export.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['id', 'source_file', 'text', 'embedding_json'])

    docs = res.get('documents', [])
    metas = res.get('metadatas', [])
    embs = res.get('embeddings', [])

    for idx in range(len(docs)):
        meta = metas[idx] if idx < len(metas) else {}
        doc = docs[idx]
        emb_vec = embs[idx] if idx < len(embs) else None

        # Convert embedding arrays to JSON-serializable lists safely
        emb_json = ''
        if emb_vec is not None:
            try:
                emb_list = emb_vec.tolist() if hasattr(emb_vec, 'tolist') else list(emb_vec)
                emb_json = json.dumps(emb_list)
            except Exception:
                try:
                    emb_json = json.dumps(list(emb_vec))
                except Exception:
                    emb_json = ''

        writer.writerow([
            idx,
            meta.get('source_file', ''),
            doc.replace('\n', ' '),
            emb_json
        ])

print(f"Saved {len(docs)} rows to data/chroma_export.csv")