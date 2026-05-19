import logging
from typing import Generator
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHUNK_SIZE = 512  # tokens (approximate)
CHUNK_OVERLAP = 50


def estimate_tokens(text: str) -> int:
    """Rough token estimation: ~4 chars per token."""
    return len(text) // 4


def chunk_section(section: dict, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list:
    """Split a section into overlapping chunks."""
    text = section["section_text"]

    # Convert token-based sizes to char-based (rough: 4 chars/token)
    char_size = chunk_size * 4
    char_overlap = overlap * 4

    chunks = []
    start_idx = 0
    chunk_index = 0

    while start_idx < len(text):
        end_idx = min(start_idx + char_size, len(text))

        chunk_text = text[start_idx:end_idx].strip()

        if len(chunk_text) > 100:  # Only keep substantial chunks
            chunk_id = str(uuid.uuid4())
            doc_id = f"{section['ticker']}_{section['filing_type']}_{section['filing_date'].replace('-', '')}"

            chunks.append({
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "ticker": section["ticker"],
                "company_name": section["company_name"],
                "filing_type": section["filing_type"],
                "filing_date": section["filing_date"],
                "fiscal_period": section["fiscal_period"],
                "section_name": section["section_name"],
                "text": chunk_text,
                "chunk_index": chunk_index,
                "edgar_url": section["edgar_url"],
            })

            chunk_index += 1

        # Move start index by chunk_size - overlap (sliding window)
        start_idx += char_size - char_overlap

        if start_idx >= end_idx:
            break

    return chunks


def chunk_all_sections(sections: list) -> list:
    """Chunk all sections."""
    all_chunks = []
    total_sections = len(sections)

    for i, section in enumerate(sections):
        chunks = chunk_section(section)
        all_chunks.extend(chunks)

        if (i + 1) % 10 == 0:
            logger.info(f"Chunked {i + 1}/{total_sections} sections")

    logger.info(f"✅ Created {len(all_chunks)} chunks from {total_sections} sections")
    return all_chunks


if __name__ == "__main__":
    from parse_filings import main as parse_main

    sections = parse_main()
    chunks = chunk_all_sections(sections)
