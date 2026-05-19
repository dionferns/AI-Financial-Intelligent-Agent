#!/usr/bin/env python3
"""
Phase 1 Data Pipeline Orchestrator
Runs: fetch → parse → chunk → embed → build_bm25
"""

import logging
from fetch_filings import main as fetch_main
from parse_filings import main as parse_main
from chunk import chunk_all_sections
from embed import embed_chunks, store_embeddings_in_qdrant
from build_bm25 import build_bm25_index, save_bm25_index

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_phase1():
    """Execute the entire Phase 1 pipeline."""
    logger.info("=" * 60)
    logger.info("PHASE 1: DATA PIPELINE")
    logger.info("=" * 60)

    # Task 1: Fetch filings from SEC EDGAR
    logger.info("\n📥 Task 1: Fetching filings...")
    fetch_main()

    # Task 2: Parse filings into sections
    logger.info("\n📄 Task 2: Parsing filings...")
    sections = parse_main()

    if not sections:
        logger.error("No sections parsed. Aborting pipeline.")
        return

    # Task 3: Chunk sections
    logger.info("\n✂️  Task 3: Chunking sections...")
    chunks = chunk_all_sections(sections)

    if not chunks:
        logger.error("No chunks created. Aborting pipeline.")
        return

    # Task 4: Generate embeddings and store in Qdrant
    logger.info("\n🧮 Task 4: Generating embeddings...")
    embedded_chunks = embed_chunks(chunks)

    if embedded_chunks:
        logger.info("Storing embeddings in Qdrant...")
        store_embeddings_in_qdrant(embedded_chunks)
    else:
        logger.warning("No embeddings generated. Skipping Qdrant storage.")

    # Task 5: Build BM25 keyword index
    logger.info("\n🔍 Task 5: Building BM25 index...")
    bm25, chunk_ids = build_bm25_index(chunks)

    if bm25:
        save_bm25_index(bm25, chunk_ids)
    else:
        logger.warning("BM25 index creation failed.")

    # Task 6: Verify
    logger.info("\n✅ Task 6: Verifying pipeline...")
    logger.info(f"   - Total sections parsed: {len(sections)}")
    logger.info(f"   - Total chunks created: {len(chunks)}")
    logger.info(f"   - Embeddings generated: {len(embedded_chunks)}")
    logger.info(f"   - BM25 index size: {len(chunk_ids)}")

    logger.info("\n" + "=" * 60)
    logger.info("✅ PHASE 1 COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_phase1()
