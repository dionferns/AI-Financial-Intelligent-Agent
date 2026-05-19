import logging
import os
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BATCH_SIZE = 100
EMBEDDING_MODEL = "text-embedding-3-small"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def embed_chunks(chunks: list) -> list:
    """Generate embeddings for all chunks using OpenAI."""
    if not chunks:
        logger.warning("No chunks to embed")
        return []

    embedded_chunks = []
    total_chunks = len(chunks)

    for i in range(0, total_chunks, BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        batch_texts = [chunk["text"] for chunk in batch]

        try:
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=batch_texts,
            )

            for j, embedding_obj in enumerate(response.data):
                chunk = batch[j]
                chunk["embedding"] = embedding_obj.embedding
                embedded_chunks.append(chunk)

            logger.info(f"Embedded {min(i + BATCH_SIZE, total_chunks)}/{total_chunks} chunks")

        except Exception as e:
            logger.error(f"Error embedding batch {i//BATCH_SIZE}: {e}")
            # Skip this batch and continue
            continue

    logger.info(f"✅ Generated embeddings for {len(embedded_chunks)}/{total_chunks} chunks")
    return embedded_chunks


def store_embeddings_in_qdrant(embedded_chunks: list):
    """Store embeddings in Qdrant vector database."""
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointStruct
    except ImportError:
        logger.error("qdrant-client not installed")
        return

    try:
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        client = QdrantClient(url=qdrant_url)

        collection_name = "sec_filings"

        # Create collection if not exists
        try:
            client.get_collection(collection_name)
        except:
            from qdrant_client.models import VectorParams, Distance
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=1536,  # text-embedding-3-small dimension
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"Created Qdrant collection: {collection_name}")

        # Insert points
        points = []
        for idx, chunk in enumerate(embedded_chunks):
            point = PointStruct(
                id=idx,
                vector=chunk["embedding"],
                payload={
                    "chunk_id": chunk["chunk_id"],
                    "doc_id": chunk["doc_id"],
                    "ticker": chunk["ticker"],
                    "company_name": chunk["company_name"],
                    "filing_type": chunk["filing_type"],
                    "filing_date": chunk["filing_date"],
                    "fiscal_period": chunk["fiscal_period"],
                    "section_name": chunk["section_name"],
                    "text": chunk["text"],
                    "chunk_index": chunk["chunk_index"],
                    "edgar_url": chunk["edgar_url"],
                },
            )
            points.append(point)

        # Upsert in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            client.upsert(collection_name=collection_name, points=batch)
            logger.info(f"Upserted {min(i + batch_size, len(points))}/{len(points)} points to Qdrant")

        logger.info(f"✅ Stored {len(points)} embeddings in Qdrant")

    except Exception as e:
        logger.error(f"Error storing embeddings in Qdrant: {e}")


if __name__ == "__main__":
    from chunk import chunk_all_sections
    from parse_filings import main as parse_main

    sections = parse_main()
    chunks = chunk_all_sections(sections)
    embedded_chunks = embed_chunks(chunks)
    store_embeddings_in_qdrant(embedded_chunks)
