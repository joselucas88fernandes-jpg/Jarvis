"""
Local Vector Database — LanceDB + sentence-transformers
========================================================
Fully offline: no API calls, no Gemini, no internet required.
Uses all-MiniLM-L6-v2 (384-dim) for embedding generation.
"""

import sys
import threading
from datetime import datetime
from pathlib import Path

import numpy as np

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
DB_PATH  = BASE_DIR / "memory" / "lancedb"

# ── Model singleton ────────────────────────────────────────────────────────────
_model      = None
_model_lock = threading.Lock()

def _get_model():
    global _model
    if _model is not None:
        return _model
    with _model_lock:
        if _model is None:
            try:
                from sentence_transformers import SentenceTransformer
                print("[VectorDB] 📦 Loading sentence-transformer model…")
                _model = SentenceTransformer("all-MiniLM-L6-v2")
                print("[VectorDB] ✅ Model loaded (all-MiniLM-L6-v2, 384-dim)")
            except Exception as e:
                print(f"[VectorDB] ❌ Model load failed: {e}")
                _model = None
    return _model


def generate_embedding(text: str) -> list[float]:
    """Return 384-dim embedding vector for *text*, or zero vector on failure."""
    model = _get_model()
    if model is None:
        return [0.0] * 384
    try:
        vec = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return vec.tolist()
    except Exception as e:
        print(f"[VectorDB] ⚠️ Embedding error: {e}")
        return [0.0] * 384


# ── LanceDB helpers ────────────────────────────────────────────────────────────
_db_lock = threading.Lock()

def _get_db():
    try:
        import lancedb
        DB_PATH.mkdir(parents=True, exist_ok=True)
        return lancedb.connect(str(DB_PATH))
    except ImportError:
        raise RuntimeError("lancedb not installed — run: pip install lancedb")


def _get_table():
    """Open or create the 'memories' table."""
    import pyarrow as pa

    schema = pa.schema([
        pa.field("id",           pa.int64()),
        pa.field("key",          pa.utf8()),
        pa.field("value",        pa.utf8()),
        pa.field("category",     pa.utf8()),
        pa.field("vector",       pa.list_(pa.float32(), 384)),
        pa.field("access_count", pa.int64()),
        pa.field("updated",      pa.utf8()),
    ])

    db = _get_db()
    if "memories" not in db.table_names():
        # Create with empty seed row then delete it so schema is registered
        import pandas as pd
        seed = pd.DataFrame([{
            "id": 0, "key": "__init__", "value": "__init__",
            "category": "__init__",
            "vector": [0.0] * 384,
            "access_count": 0,
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }])
        tbl = db.create_table("memories", data=seed, schema=schema)
        tbl.delete("key = '__init__'")
        return tbl
    return db.open_table("memories")


def _next_id() -> int:
    try:
        tbl = _get_table()
        df  = tbl.to_pandas()
        if df.empty:
            return 1
        return int(df["id"].max()) + 1
    except Exception:
        return 1


# ── Public API (same interface as old SQLite version) ─────────────────────────

def initialize_db():
    """Ensure LanceDB table exists (called lazily, but can be called explicitly)."""
    try:
        _get_table()
    except Exception as e:
        print(f"[VectorDB] ⚠️ DB init error: {e}")


def add_memory(key: str, value: str, category: str):
    """Embed and store a memory entry."""
    with _db_lock:
        try:
            combined = f"{key}: {value}"
            vector   = generate_embedding(combined)
            tbl      = _get_table()
            tbl.add([{
                "id":           _next_id(),
                "key":          key,
                "value":        value,
                "category":     category,
                "vector":       [float(v) for v in vector],
                "access_count": 0,
                "updated":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }])
            print(f"[VectorDB] 💾 Stored: {category}/{key}")
        except Exception as e:
            print(f"[VectorDB] ❌ add_memory error: {e}")


def delete_memory(memory_id: int):
    """Delete a memory entry by its integer id."""
    with _db_lock:
        try:
            _get_table().delete(f"id = {memory_id}")
        except Exception as e:
            print(f"[VectorDB] ❌ delete_memory error: {e}")


def get_all_memories() -> list[dict]:
    """Return all stored memories as a list of dicts (no vectors)."""
    try:
        df = _get_table().to_pandas()
        if df.empty:
            return []
        records = []
        for _, row in df.iterrows():
            records.append({
                "id":           int(row["id"]),
                "key":          str(row["key"]),
                "value":        str(row["value"]),
                "category":     str(row["category"]),
                "access_count": int(row["access_count"]),
                "updated":      str(row["updated"]),
            })
        return records
    except Exception as e:
        print(f"[VectorDB] ⚠️ get_all_memories error: {e}")
        return []


def increment_access(memory_id: int):
    """Increment the access_count for a memory entry."""
    try:
        tbl = _get_table()
        df  = tbl.to_pandas()
        mask = df["id"] == memory_id
        if mask.any():
            new_count = int(df.loc[mask, "access_count"].iloc[0]) + 1
            tbl.update(f"id = {memory_id}", {"access_count": new_count})
    except Exception as e:
        print(f"[VectorDB] ⚠️ increment_access error: {e}")


def query_memories(query_text: str, category: str = None, top_k: int = 5) -> list[dict]:
    """
    Find the top-k most semantically similar memories using LanceDB vector search.
    Optionally filter by category.
    """
    try:
        query_vector = generate_embedding(query_text)
        if all(v == 0.0 for v in query_vector):
            return []

        tbl      = _get_table()
        limit    = top_k * 4 if category else top_k * 2
        raw      = tbl.search(query_vector).limit(limit).to_list()

        results = []
        for row in raw:
            if category and row.get("category") != category:
                continue
            results.append({
                "id":           int(row["id"]),
                "key":          str(row["key"]),
                "value":        str(row["value"]),
                "category":     str(row["category"]),
                "access_count": int(row["access_count"]),
                "updated":      str(row["updated"]),
                "similarity":   float(1.0 - row.get("_distance", 0.0)),
            })
            if len(results) >= top_k:
                break

        # Bump access counts
        for item in results:
            threading.Thread(
                target=increment_access, args=(item["id"],), daemon=True
            ).start()

        return results

    except Exception as e:
        print(f"[VectorDB] ⚠️ query_memories error: {e}")
        return []
