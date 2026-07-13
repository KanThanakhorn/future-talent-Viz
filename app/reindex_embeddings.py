from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone

from .config import settings
from .db import connect, init_db
from .embeddings import embed_passages

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
LOG = logging.getLogger("embedding-migration")


def migrate(batch_size: int = 32, activate: bool = True) -> dict:
    """Build a separate v2 index, verify it, then atomically activate it."""
    init_db()
    model = settings.embedding_model
    with connect() as conn:
        chunks = conn.execute("SELECT id,content FROM chunks ORDER BY id").fetchall()
        conn.execute(
            """INSERT INTO embedding_indexes(model,dimension,status,chunk_count)
               VALUES(?,0,'building',0)
               ON CONFLICT(model) DO UPDATE SET status='building',chunk_count=0,activated_at=NULL""",
            (model,),
        )
        conn.execute("DELETE FROM chunk_embeddings_v2 WHERE model=?", (model,))
        conn.commit()
    dimension = 0
    try:
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            vectors = embed_passages([row["content"] for row in batch])
            if not vectors or len(vectors) != len(batch):
                raise RuntimeError("Embedding model returned an incomplete batch")
            dimension = len(vectors[0])
            if dimension < 300 or any(len(vector) != dimension for vector in vectors):
                raise RuntimeError("Embedding dimension validation failed")
            with connect() as conn:
                conn.executemany(
                    "INSERT INTO chunk_embeddings_v2(chunk_id,model,embedding) VALUES(?,?,?)",
                    [(row["id"], model, json.dumps(vector, separators=(",", ":"))) for row, vector in zip(batch, vectors)],
                )
            LOG.info("Embedded %s/%s chunks", min(start + len(batch), len(chunks)), len(chunks))
        with connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM chunk_embeddings_v2 WHERE model=?", (model,)).fetchone()[0]
            if count != len(chunks):
                raise RuntimeError(f"Index verification failed: expected {len(chunks)}, found {count}")
            conn.execute(
                "UPDATE embedding_indexes SET dimension=?,status='ready',chunk_count=? WHERE model=?",
                (dimension, count, model),
            )
            if activate:
                conn.execute(
                    """INSERT INTO system_settings(key,value,updated_at) VALUES('active_embedding_model',?,CURRENT_TIMESTAMP)
                       ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=CURRENT_TIMESTAMP""",
                    (model,),
                )
                conn.execute(
                    "UPDATE embedding_indexes SET activated_at=? WHERE model=?",
                    (datetime.now(timezone.utc).isoformat(), model),
                )
        return {"model": model, "dimension": dimension, "chunks": len(chunks), "active": activate}
    except Exception:
        with connect() as conn:
            conn.execute("UPDATE embedding_indexes SET status='failed' WHERE model=?", (model,))
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and verify the multilingual embedding index")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--no-activate", action="store_true")
    args = parser.parse_args()
    print(json.dumps(migrate(args.batch_size, not args.no_activate), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
