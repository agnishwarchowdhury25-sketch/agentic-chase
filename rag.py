import chromadb

store = chromadb.PersistentClient(path="chroma_db")

def index_chat(chat_id, df, size=25):
    try:
        store.delete_collection(f"chat_{chat_id}")
    except Exception:
        pass
    col = store.create_collection(f"chat_{chat_id}")
    ids, docs, metas = [], [], []
    for i in range(0, len(df), size):
        part = df.iloc[i:i + size]
        text = "\n".join(f"[{chat_id}-{r.id}] {r.sender}: {r.text}" for r in part.itertuples())
        ids.append(f"{chat_id}_{i}")
        docs.append(text)
        metas.append({"start": str(part.ts.iloc[0]), "end": str(part.ts.iloc[-1])})
    for j in range(0, len(ids), 100):
        col.add(ids=ids[j:j + 100], documents=docs[j:j + 100], metadatas=metas[j:j + 100])

def retrieve(chat_id, query, k=8, spread=False):
    col = store.get_collection(f"chat_{chat_id}")
    docs = col.query(query_texts=[query], n_results=min(k, col.count()))["documents"][0]
    if spread:
        allc = col.get(include=["documents"])["documents"]
        step = max(1, len(allc) // 6)
        docs += allc[::step][:6]
    return docs

def delete_index(chat_id):
    try:
        store.delete_collection(f"chat_{chat_id}")
    except Exception:
        pass