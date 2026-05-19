import logging
import pickle
from pathlib import Path
from rank_bm25 import BM25Okapi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"


def build_bm25_index(chunks: list):
    """Build BM25 keyword search index from chunks."""
    if not chunks:
        logger.warning("No chunks to index")
        return None, []

    try:
        # Tokenize chunk texts
        tokenized_corpus = []
        chunk_ids = []

        for chunk in chunks:
            text = chunk["text"]
            # Simple whitespace + punctuation tokenization
            tokens = text.lower().split()
            tokenized_corpus.append(tokens)
            chunk_ids.append(chunk["chunk_id"])

        # Build BM25 index
        bm25 = BM25Okapi(tokenized_corpus)

        logger.info(f"✅ Built BM25 index for {len(chunks)} chunks")

        return bm25, chunk_ids

    except Exception as e:
        logger.error(f"Error building BM25 index: {e}")
        return None, []


def save_bm25_index(bm25: BM25Okapi, chunk_ids: list):
    """Serialize BM25 index and chunk IDs to disk."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Save BM25 index
        with open(DATA_DIR / "bm25_index.pkl", "wb") as f:
            pickle.dump(bm25, f)

        # Save chunk IDs in order
        with open(DATA_DIR / "bm25_corpus_ids.pkl", "wb") as f:
            pickle.dump(chunk_ids, f)

        logger.info(f"✅ Saved BM25 index and corpus IDs to {DATA_DIR}")

    except Exception as e:
        logger.error(f"Error saving BM25 index: {e}")


if __name__ == "__main__":
    from chunk import chunk_all_sections
    from parse_filings import main as parse_main

    sections = parse_main()
    chunks = chunk_all_sections(sections)
    bm25, chunk_ids = build_bm25_index(chunks)
    if bm25:
        save_bm25_index(bm25, chunk_ids)
