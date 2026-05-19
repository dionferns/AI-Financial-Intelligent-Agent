from sqlalchemy import Column, Integer, String, Text, Date, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Filing(Base):
    __tablename__ = "filings"

    id = Column(Integer, primary_key=True)
    doc_id = Column(String, unique=True, nullable=False)
    ticker = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    filing_type = Column(String, nullable=False)  # 10-K, 10-Q
    filing_date = Column(Date, nullable=False)
    fiscal_period = Column(String, nullable=False)  # FY2024, Q3 2024
    section_name = Column(String, nullable=False)
    full_text = Column(Text, nullable=False)
    edgar_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Chunk(Base):
    __tablename__ = "chunks"

    chunk_id = Column(String, primary_key=True)
    doc_id = Column(String, ForeignKey("filings.doc_id"), nullable=False)
    ticker = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    filing_type = Column(String, nullable=False)
    filing_date = Column(Date, nullable=False)
    fiscal_period = Column(String, nullable=False)
    section_name = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    edgar_url = Column(String, nullable=False)


class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=True)
    question = Column(Text, nullable=False)
    ticker_filter = Column(String, nullable=True)
    filing_type_filter = Column(String, nullable=True)
    answer = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=False)
    out_of_scope = Column(Integer, nullable=False, default=0)  # 0 or 1
    cached = Column(Integer, nullable=False, default=0)
    latency_ms = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
