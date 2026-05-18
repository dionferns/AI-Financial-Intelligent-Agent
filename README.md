# PROJECT 1: AI FINANCIAL INTELLIGENCE AGENT
### Complete Build Specification for an LLM / Engineer
### Multi-Agent RAG System over SEC Filings

---

## HOW TO READ THIS DOCUMENT

This document is fully self-contained. No prior context is needed. It contains everything required to build a production-grade AI financial intelligence agent from scratch — architecture, tech stack, data sources, folder structure, phase-by-phase build instructions, evaluation strategy, deployment, and CV framing.

**Target builder:** An LLM or engineer with access to Python 3.11+, Node.js 18+, a terminal, Docker, and cloud service accounts (OpenAI/Anthropic, Cohere, LangSmith, Vercel, Railway).

**Goal:** Produce a portfolio project that demonstrates senior-level AI engineering skills — specifically RAG systems, multi-agent orchestration, hybrid retrieval, structured outputs, evaluation frameworks, and full-stack software engineering — suitable for roles at top-tier tech companies (Palantir, Bloomberg, Stripe, Cohere, Glean, Google, Microsoft, or any forward-deployed AI engineering role).

---

## Project Summary

A production-grade, multi-agent RAG system that allows users to ask complex financial questions and receive structured answers grounded exclusively in real, official SEC filings — with company citations (ticker, filing type, section, date), confidence scores, and a visible agent reasoning trace.

**Domain:** Financial research — SEC EDGAR filings (10-K annual reports, 10-Q quarterly reports, 8-K material event disclosures, S-1 IPO filings)

**Why this domain:**
- Every major tech and enterprise company cares deeply about financial document intelligence
- Hallucination in financial context means wrong figures, misattributed statements, or incorrect filing periods — immediately understood by interviewers as a hard, high-stakes problem
- SEC EDGAR is a completely free, official, massive public API requiring no API key
- Forward deployed engineer roles at companies like Palantir, Glean, and Cohere frequently involve exactly this class of document intelligence system
- Bloomberg, FactSet, and dozens of fintech startups are actively building versions of this — it is a real, commercially valuable product

---

## What the System Must Do

1. Accept a natural language financial question from a user via a web UI or REST API.
2. Allow users to optionally filter by: company ticker (e.g. AAPL), filing type (10-K / 10-Q / 8-K), and date range.
3. Retrieve the most relevant SEC filing chunks from a vector + keyword hybrid search system.
4. Pass retrieved context through a multi-agent reasoning pipeline that decides whether to search more, synthesise, or ask for clarification.
5. Return a fully structured response containing:
   - A direct, grounded answer to the financial question
   - Citations: company name, ticker, filing type, filing date, section name (e.g. "Risk Factors", "MD&A"), chunk reference, and a direct link to the SEC EDGAR filing
   - A confidence score (0.0–1.0)
   - An expandable reasoning trace showing each agent's reasoning step
6. Refuse or flag out-of-scope questions (e.g. questions not answerable from the available filings) gracefully with a helpful message.
7. Cache repeated queries using Redis to avoid unnecessary LLM calls.
8. Log all queries and responses to a PostgreSQL database.
9. Be fully observable — every agent step must be traceable via LangSmith.
10. Pass an automated DeepEval test suite on every code change via GitHub Actions CI/CD.
11. Be deployable via Docker Compose locally and to a cloud environment in production.

---

## Example Queries the System Must Handle

- *"What are Apple's main revenue risks mentioned in their 2024 10-K?"*
- *"How has Microsoft's cloud revenue grown over the last three annual reports?"*
- *"What did Nvidia say about supply chain risks in their most recent quarterly filing?"*
- *"Compare the liquidity positions of Google and Meta from their latest 10-Qs"*
- *"What were the material events disclosed by Tesla in their 8-K filings in 2024?"*
- *"What is Amazon's stated strategy for AWS growth according to their most recent 10-K?"*
- *"What risk factors does OpenAI's S-1 cite regarding competition?"*

---

## Architecture

```
User
 │
 ▼
Next.js 14 Frontend (TypeScript)
 │  Ticker search box + filing type filter + date range selector
 │  REST calls via React Query
 ▼
FastAPI Gateway (Python)
 │          │
 │       Redis Cache (repeated query short-circuit, 1hr TTL)
 │
 ▼
LangGraph Orchestrator
 ├── Node 1: Router Agent
 │     Decides:
 │       - Is this question answerable from available filings?
 │       - Single company or multi-company comparison?
 │       - Single-hop or multi-hop retrieval needed?
 │       - Out of scope?
 │
 ├── Node 2: Retriever Agent
 │     Tools available:
 │       - search_filings(query, ticker?, filing_type?, top_k)
 │           → Qdrant semantic search with metadata filters
 │       - keyword_search(query, ticker?, top_k)
 │           → BM25 keyword search
 │       - rerank_results(query, chunks)
 │           → RRF fusion + Cohere cross-encoder rerank
 │       - get_full_section(doc_id, section_name)
 │           → fetch full section text from PostgreSQL
 │           (e.g. fetch entire "Risk Factors" section)
 │
 ├── Node 3: Reasoning Agent
 │     Chain-of-thought financial reasoning over retrieved chunks
 │     Identifies: figures, dates, filing periods, company attributions
 │     Decides: Is evidence sufficient? Need another retrieval pass?
 │     For multi-company: runs parallel reasoning per company
 │
 └── Node 4: Synthesizer Agent
       Produces final structured FinancialQueryResponse (Pydantic)
       Fields: answer, citations, confidence_score, reasoning_trace,
               out_of_scope_flag, filing_periods_referenced
 │
 ▼
PostgreSQL (query logs + full filing document store)
LangSmith (full agent trace observability — every step logged)
DeepEval (automated eval suite in CI — runs on every push)
```

---

## Full Technology Stack

### Languages
| Language | Used For |
|---|---|
| Python 3.11+ | All AI logic, backend API, data pipeline, evaluations |
| TypeScript | Frontend (Next.js 14), type-safe API contracts |

### AI / LLM Layer
| Tool | Version / Model | Purpose |
|---|---|---|
| LangGraph | latest | Multi-agent state machine orchestration |
| LlamaIndex | latest | Document ingestion pipeline, chunking, hybrid retrieval |
| OpenAI API | gpt-4o for reasoning; text-embedding-3-small for embeddings | LLM backbone and vector embeddings |
| OR Anthropic API | claude-sonnet-4-20250514 | Alternative LLM backbone (same interface) |
| Pydantic v2 | latest | Structured output schemas for all agent responses |
| Cohere Rerank API | rerank-english-v3.0 | Cross-encoder reranking of retrieved chunks |
| LangSmith | latest | LLM observability — full agent step tracing and logging |

### Retrieval & Search
| Tool | Purpose |
|---|---|
| Qdrant | Vector database for semantic search — self-hosted via Docker |
| rank_bm25 (Python library) | Keyword-based sparse retrieval (BM25 algorithm) |
| Reciprocal Rank Fusion (RRF) | Fuse results from semantic + keyword search into single ranked list |
| Cohere Rerank | Final cross-encoder reranking pass for precision |

### Backend
| Tool | Purpose |
|---|---|
| FastAPI | REST API server |
| Pydantic v2 | Request and response validation |
| Redis | Query result caching (TTL: 1 hour) |
| PostgreSQL | Full filing document store, query logs, user sessions |
| SQLAlchemy | ORM for PostgreSQL |
| Alembic | Database schema migrations |
| Uvicorn | ASGI server for FastAPI |
| httpx | Async HTTP client for internal service calls |

### Evaluation Framework
| Tool | Purpose |
|---|---|
| DeepEval | Primary eval framework — pytest-native LLM evaluation with built-in and custom metrics |
| RAGAS | RAG-specific retrieval quality metrics (run locally, complements DeepEval) |
| pytest | Test runner (DeepEval integrates natively as pytest plugin) |

### Frontend
| Tool | Purpose |
|---|---|
| Next.js 14 with App Router | React framework |
| TypeScript | Full type safety across frontend |
| Tailwind CSS | Utility-first styling |
| shadcn/ui | Pre-built accessible component library |
| TanStack Query (React Query) | API state management, caching, loading and error states |

### DevOps / Infrastructure
| Tool | Purpose |
|---|---|
| Docker + Docker Compose | Containerise all services for local and production deployment |
| GitHub Actions | CI/CD — run tests and evals on every push, deploy on merge to main |
| Vercel | Frontend deployment (free tier sufficient) |
| Railway or Render | Backend + database + Redis deployment |

---

## Data Source: SEC EDGAR

### About SEC EDGAR
- **URL:** https://www.sec.gov/cgi-bin/browse-edgar
- **Full-text search API:** https://efts.sec.gov/LATEST/search-index?q=...
- **Bulk filing index:** https://www.sec.gov/Archives/edgar/full-index/
- **Content:** Every public company filing in the US since 1993 — 10-K, 10-Q, 8-K, S-1, and more
- **Cost:** Completely free. No API key required.
- **Rate limit:** Maximum 10 requests per second — must implement rate limiting in pipeline
- **Format:** Filings are HTML or plain text; metadata available as JSON via EDGAR APIs

### Recommended Starting Corpus
To keep the project manageable, start with a focused corpus:
- **Companies:** Top 50 S&P 500 companies by market cap (Apple, Microsoft, Nvidia, Alphabet, Amazon, Meta, Tesla, Berkshire, etc.)
- **Filing types:** 10-K (annual) and 10-Q (quarterly) only — these contain the richest content
- **Date range:** Last 3 years (2022–2025) — gives multi-period comparison capability
- **Target size:** ~500–1,000 filings, ~200,000–500,000 chunks after processing

### Key Filing Sections to Extract and Index
Each 10-K and 10-Q has standard sections — extract and tag these explicitly:
| Section | Content |
|---|---|
| Item 1 — Business | Company description, products, strategy |
| Item 1A — Risk Factors | All stated risk factors |
| Item 7 — MD&A | Management's Discussion and Analysis of financial results |
| Item 8 — Financial Statements | Balance sheet, income statement, cash flow |
| Item 9A — Controls | Internal controls and disclosures |

Tagging sections as metadata on each chunk enables the Retriever Agent to use `get_full_section(doc_id, "Risk Factors")` to fetch entire sections when needed.

### EDGAR API Endpoints Used
```
# Search for filings by company and type
GET https://data.sec.gov/submissions/CIK{cik_number}.json
# Returns: all filings for a company with metadata

# Download a specific filing
GET https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/{filename}.htm

# Full-text search across all filings
GET https://efts.sec.gov/LATEST/search-index?q={query}&dateRange=custom&startdt={date}&enddt={date}&forms=10-K
```

---

## Pydantic Schemas

These schemas are used across the entire system — agents, API, and frontend.

```python
# schemas/financial.py

from pydantic import BaseModel
from typing import Optional
from datetime import date

class FilingCitation(BaseModel):
    company_name: str              # e.g. "Apple Inc."
    ticker: str                    # e.g. "AAPL"
    filing_type: str               # e.g. "10-K", "10-Q", "8-K"
    filing_date: str               # e.g. "2024-10-31"
    fiscal_period: str             # e.g. "FY2024", "Q3 2024"
    section: str                   # e.g. "Risk Factors", "MD&A"
    chunk_id: str                  # Internal chunk reference
    relevance_score: float         # 0.0–1.0
    edgar_url: str                 # Direct link to filing on SEC EDGAR

class FinancialQueryRequest(BaseModel):
    question: str
    ticker_filter: Optional[str] = None        # e.g. "AAPL" — restrict to one company
    filing_type_filter: Optional[str] = None   # e.g. "10-K"
    date_from: Optional[str] = None            # e.g. "2023-01-01"
    date_to: Optional[str] = None              # e.g. "2024-12-31"
    user_id: Optional[str] = None

class FinancialQueryResponse(BaseModel):
    answer: str
    citations: list[FilingCitation]
    confidence_score: float                    # 0.0–1.0
    reasoning_trace: list[str]                 # Each agent's reasoning steps
    filing_periods_referenced: list[str]       # e.g. ["FY2024 10-K", "Q3 2024 10-Q"]
    out_of_scope: bool
    cached: bool
    latency_ms: int

class AgentState(TypedDict):
    query: str
    ticker_filter: str | None
    filing_type_filter: str | None
    retrieved_chunks: list[dict]
    reasoning_steps: list[str]
    final_answer: str | None
    citations: list[FilingCitation]
    confidence_score: float
    out_of_scope: bool
    is_multi_company: bool
    iteration_count: int
```

---

## Folder Structure

```
financial-agent/
├── backend/
│   ├── app/
│   │   ├── main.py                        # FastAPI app entrypoint, CORS, lifespan
│   │   ├── routers/
│   │   │   ├── query.py                   # POST /query
│   │   │   ├── filings.py                 # GET /filings?ticker=AAPL (list available filings)
│   │   │   ├── history.py                 # GET /history
│   │   │   └── health.py                  # GET /health
│   │   ├── agents/
│   │   │   ├── graph.py                   # LangGraph state machine — nodes + edges
│   │   │   ├── router_agent.py            # Node 1: classify query type and routing
│   │   │   ├── retriever_agent.py         # Node 2: hybrid retrieval tools
│   │   │   ├── reasoning_agent.py         # Node 3: financial chain-of-thought
│   │   │   └── synthesizer_agent.py       # Node 4: structured output generation
│   │   ├── retrieval/
│   │   │   ├── qdrant_client.py           # Semantic vector search with metadata filters
│   │   │   ├── bm25_index.py              # BM25 keyword search
│   │   │   ├── hybrid_search.py           # RRF fusion of semantic + keyword results
│   │   │   └── reranker.py                # Cohere cross-encoder reranking
│   │   ├── schemas/
│   │   │   └── financial.py               # All Pydantic models (above)
│   │   ├── db/
│   │   │   ├── models.py                  # SQLAlchemy: QueryLog, Filing, Chunk tables
│   │   │   ├── session.py                 # DB session management
│   │   │   └── migrations/                # Alembic migration files
│   │   └── cache/
│   │       └── redis_client.py            # Redis get/set with TTL
│   ├── Dockerfile
│   └── requirements.txt
│
├── pipeline/
│   ├── fetch_filings.py                   # Download filings from SEC EDGAR API
│   ├── parse_filings.py                   # Extract sections from HTML/text filings
│   ├── chunk.py                           # Chunk with section metadata preservation
│   ├── embed.py                           # Generate embeddings, store in Qdrant
│   └── build_bm25.py                      # Build and serialise BM25 index
│
├── evals/
│   ├── datasets/
│   │   ├── golden_dataset.json            # 100 verified financial Q&A pairs
│   │   └── edge_cases.json                # Out-of-scope, ambiguous, multi-company queries
│   ├── tests/
│   │   ├── test_retrieval.py              # ContextualPrecision, ContextualRecall
│   │   ├── test_agent_output.py           # Faithfulness, Hallucination, AnswerRelevancy
│   │   ├── test_financial_accuracy.py     # Custom FinancialAnalystAccuracy GEval
│   │   └── test_edge_cases.py             # Out-of-scope handling, refusal behaviour
│   └── conftest.py                        # Shared pytest fixtures
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx                       # Main chat/query UI
│   │   ├── layout.tsx
│   │   └── components/
│   │       ├── QueryInput.tsx             # Question text area + submit
│   │       ├── FilingFilters.tsx          # Ticker search + filing type + date range
│   │       ├── AnswerCard.tsx             # Answer text display
│   │       ├── CitationList.tsx           # Filing citations with EDGAR links
│   │       ├── ReasoningTrace.tsx         # Collapsible agent reasoning steps
│   │       └── ConfidenceBar.tsx          # Visual 0–100% confidence indicator
│   ├── lib/
│   │   └── api.ts                         # React Query hooks
│   ├── tailwind.config.ts
│   └── package.json
│
├── docker-compose.yml                     # Services: api + qdrant + postgres + redis
├── .github/
│   └── workflows/
│       ├── ci.yml                         # pytest + DeepEval on every push
│       └── deploy.yml                     # Deploy on merge to main
├── README.md
└── EVALS.md                               # Eval scores across build iterations
```

---

## Step-by-Step Build Phases

---

### Phase 1 — Data Pipeline (Days 1–7)

**Goal:** Download, parse, chunk, embed, and index SEC filings into the retrieval system.

#### Task 1: Write `pipeline/fetch_filings.py`

This script downloads filings for the target company list from SEC EDGAR.

Steps:
- Define target tickers: AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA, BRK-B, JPM, V (start with 10 companies, expand later)
- For each ticker:
  - Look up CIK (Central Index Key) from: `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company={ticker}&type=10-K&dateb=&owner=include&count=10&search_text=`
  - Call `https://data.sec.gov/submissions/CIK{cik}.json` to get filing history
  - Filter for 10-K and 10-Q filings from the last 3 years
  - Download each filing's primary document (HTML)
  - Save locally: `data/raw/{ticker}/{filing_type}_{date}.html`
- Implement rate limiting: `time.sleep(0.1)` between requests (max 10 req/sec)
- Log progress: how many filings downloaded per company

#### Task 2: Write `pipeline/parse_filings.py`

Parse the raw HTML filings into structured text with section metadata.

Steps:
- Use `BeautifulSoup4` to parse HTML filings
- Identify standard section boundaries using heading patterns:
  - Search for: "Item 1.", "Item 1A.", "Item 7.", "Item 8.", "Item 9A."
  - Extract the text between section headers
- Clean text: remove HTML tags, normalise whitespace, remove page headers/footers/boilerplate
- For each parsed filing, output a list of section objects:
  ```python
  {
    "ticker": "AAPL",
    "company_name": "Apple Inc.",
    "filing_type": "10-K",
    "filing_date": "2024-10-31",
    "fiscal_period": "FY2024",
    "section_name": "Risk Factors",
    "section_text": "...",
    "edgar_url": "https://www.sec.gov/Archives/edgar/data/..."
  }
  ```
- Store full parsed sections in PostgreSQL: table `filings` with columns matching the above
- Assign each filing a unique `doc_id`

#### Task 3: Write `pipeline/chunk.py`

Chunk parsed sections into retrieval-optimised pieces.

Steps:
- Use LlamaIndex `RecursiveCharacterTextSplitter`
- Chunk size: 512 tokens, overlap: 50 tokens
- Preserve all section metadata on every chunk:
  ```python
  {
    "chunk_id": "aapl_10k_2024_riskfactors_chunk_003",
    "doc_id": "aapl_10k_2024",
    "ticker": "AAPL",
    "company_name": "Apple Inc.",
    "filing_type": "10-K",
    "filing_date": "2024-10-31",
    "fiscal_period": "FY2024",
    "section_name": "Risk Factors",
    "text": "...",
    "edgar_url": "..."
  }
  ```
- Store all chunks in PostgreSQL: table `chunks`

#### Task 4: Write `pipeline/embed.py`

Generate embeddings and populate Qdrant.

Steps:
- Call OpenAI `text-embedding-3-small` API in batches of 100
- For each chunk: embed the text, store vector + all metadata in Qdrant
- Qdrant collection name: `sec_filings`
- Qdrant payload fields (for filtering): `ticker`, `filing_type`, `filing_date`, `section_name`
- This enables filtered search: e.g. search only within AAPL's 10-K filings

#### Task 5: Write `pipeline/build_bm25.py`

Build keyword search index.

Steps:
- Load all chunk texts from PostgreSQL
- Tokenise using whitespace + punctuation splitting
- Build BM25 index using `rank_bm25` library (`BM25Okapi`)
- Serialise index to disk: `data/bm25_index.pkl`
- Store chunk_id list in same order as BM25 corpus: `data/bm25_corpus_ids.pkl`

#### Task 6: Verify Pipeline End-to-End

- Confirm Qdrant collection has expected vector count
- Run a test query against Qdrant — verify top results are relevant
- Load BM25 index and run a test keyword query — verify results
- Check PostgreSQL has full filing text retrievable by doc_id
- Log: total filings, total chunks, total vectors

---

### Phase 2 — Core Retrieval Pipeline (Days 8–14)

**Goal:** Build and validate the hybrid retrieval system before adding agents.

#### Task 1: Write `retrieval/qdrant_client.py`

```python
def semantic_search(
    query: str,
    top_k: int = 20,
    ticker_filter: str | None = None,
    filing_type_filter: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None
) -> list[Chunk]:
    # 1. Embed query using text-embedding-3-small
    # 2. Build Qdrant filter from optional metadata filters
    # 3. Query Qdrant collection with vector + filter
    # 4. Return top_k chunks with scores and metadata
```

#### Task 2: Write `retrieval/bm25_index.py`

```python
def keyword_search(
    query: str,
    top_k: int = 20,
    ticker_filter: str | None = None
) -> list[Chunk]:
    # 1. Load BM25 index and corpus IDs from disk
    # 2. Tokenise query
    # 3. Get BM25 scores for all documents
    # 4. Apply ticker filter (post-filter by metadata)
    # 5. Return top_k chunks sorted by BM25 score
```

#### Task 3: Write `retrieval/hybrid_search.py`

Implement Reciprocal Rank Fusion (RRF):

```python
def hybrid_search(
    query: str,
    top_k: int = 20,
    **filters
) -> list[Chunk]:
    semantic_results = semantic_search(query, top_k=top_k*2, **filters)
    keyword_results = keyword_search(query, top_k=top_k*2, **filters)

    # RRF formula: score(d) = sum(1 / (k + rank(d)))  where k=60
    # Combine rankings from both lists
    # Deduplicate by chunk_id
    # Return top_k chunks sorted by fused RRF score
```

#### Task 4: Write `retrieval/reranker.py`

```python
def rerank(
    query: str,
    chunks: list[Chunk],
    top_n: int = 10
) -> list[Chunk]:
    # Call Cohere Rerank API
    # Input: query + list of chunk texts
    # Output: top_n chunks sorted by cross-encoder relevance score
    # Model: rerank-english-v3.0
```

#### Task 5: Run RAGAS Baseline Evaluation

Before adding agents, measure retrieval quality alone:
- Create 20 test queries with known relevant chunks
- Run hybrid_search + rerank pipeline
- Measure with RAGAS: `ContextualPrecision`, `ContextualRecall`, `ContextualRelevancy`
- Record baseline scores in `EVALS.md` — these are your "before agents" benchmark

---

### Phase 3 — Multi-Agent Layer with LangGraph (Days 15–21)

**Goal:** Build the full 4-node agent state machine.

#### Task 1: Define AgentState in `agents/graph.py`

```python
from typing import TypedDict

class AgentState(TypedDict):
    query: str
    ticker_filter: str | None
    filing_type_filter: str | None
    retrieved_chunks: list[dict]
    reasoning_steps: list[str]
    final_answer: str | None
    citations: list[FilingCitation]
    confidence_score: float
    out_of_scope: bool
    is_multi_company: bool       # True if query compares multiple companies
    iteration_count: int         # Max 2 retrieval iterations
```

#### Task 2: Build `agents/router_agent.py` (Node 1)

The Router Agent classifies every incoming query before any retrieval happens.

Logic:
- Input: raw query + optional filters
- Use LLM to classify into one of:
  - `SINGLE_COMPANY_SINGLE_HOP`: e.g. "What are Apple's risk factors?"
  - `SINGLE_COMPANY_MULTI_HOP`: e.g. "How has Apple's revenue changed over 3 years?" (needs multiple filings)
  - `MULTI_COMPANY_COMPARISON`: e.g. "Compare Google and Meta's cash positions"
  - `OUT_OF_SCOPE`: e.g. "What is the stock price of Apple?" (not in filings)
- Set `is_multi_company=True` for MULTI_COMPANY_COMPARISON
- Set `out_of_scope=True` and route directly to Synthesizer for OUT_OF_SCOPE
- Pass classification result downstream in AgentState

#### Task 3: Build `agents/retriever_agent.py` (Node 2)

The Retriever Agent has access to 4 tools and decides which to call:

Tool definitions (LangGraph tool format):
```python
@tool
def search_filings(query: str, ticker: str | None, filing_type: str | None, top_k: int = 10) -> list[Chunk]:
    """Search SEC filings using hybrid semantic + keyword retrieval with optional filters."""
    return hybrid_search(query, top_k=top_k, ticker_filter=ticker, filing_type_filter=filing_type)

@tool
def rerank_results(query: str, chunks: list[Chunk], top_n: int = 8) -> list[Chunk]:
    """Rerank retrieved chunks using Cohere cross-encoder for precision."""
    return rerank(query, chunks, top_n=top_n)

@tool
def get_full_section(doc_id: str, section_name: str) -> str:
    """Fetch the complete text of a specific section from a filing (e.g. full Risk Factors)."""
    return db.query_section(doc_id, section_name)

@tool
def keyword_search_tool(query: str, ticker: str | None, top_k: int = 10) -> list[Chunk]:
    """Keyword-only BM25 search for exact term matching in filings."""
    return keyword_search(query, top_k=top_k, ticker_filter=ticker)
```

Behaviour:
- For MULTI_COMPANY_COMPARISON: call `search_filings` once per company, merge results
- For MULTI_HOP: call `search_filings` with broad query first, then refine with specific follow-up
- Always call `rerank_results` after initial retrieval
- If `iteration_count < 2` and Reasoning Agent signals insufficient evidence: loop back

#### Task 4: Build `agents/reasoning_agent.py` (Node 3)

The Reasoning Agent performs chain-of-thought financial reasoning.

Prompt structure:
```
You are a senior financial analyst reviewing SEC filing excerpts.
Query: {query}
Retrieved filing chunks: {chunks}

Reason through this step by step:
1. Which chunks contain directly relevant information?
2. What specific figures, dates, or statements answer the query?
3. Are there any contradictions or gaps in the evidence?
4. Is the evidence sufficient to answer confidently, or do we need more retrieval?

Output your reasoning as numbered steps. End with: SUFFICIENT or NEEDS_MORE_RETRIEVAL.
```

Behaviour:
- Appends each reasoning step to `AgentState.reasoning_steps`
- If output is `NEEDS_MORE_RETRIEVAL` and `iteration_count < 2`: increment counter, route back to Retriever
- If output is `SUFFICIENT` or `iteration_count >= 2`: route to Synthesizer
- For MULTI_COMPANY: reason about each company separately, then compare

#### Task 5: Build `agents/synthesizer_agent.py` (Node 4)

The Synthesizer Agent produces the final structured response.

Tasks:
- Extract citations from chunks used in reasoning — map to `FilingCitation` Pydantic objects
- Write the final answer in plain language, grounded only in retrieved context
- Assign confidence score:
  - High (0.8–1.0): multiple relevant chunks with high rerank scores, clear answer
  - Medium (0.5–0.79): relevant chunks found but partial coverage
  - Low (0.0–0.49): limited relevant chunks, answer has uncertainty
- For OUT_OF_SCOPE: return answer = "This question cannot be answered from the available SEC filings. [helpful explanation of what filings do contain]"
- Return fully populated `FinancialQueryResponse`

#### Task 6: Wire the Graph in `agents/graph.py`

```python
from langgraph.graph import StateGraph

graph = StateGraph(AgentState)

# Add nodes
graph.add_node("router", router_agent)
graph.add_node("retriever", retriever_agent)
graph.add_node("reasoner", reasoning_agent)
graph.add_node("synthesizer", synthesizer_agent)

# Add edges
graph.set_entry_point("router")
graph.add_edge("router", "retriever")          # Unless out_of_scope → synthesizer
graph.add_edge("retriever", "reasoner")
graph.add_conditional_edges(
    "reasoner",
    lambda state: "retriever" if state["needs_more"] and state["iteration_count"] < 2 else "synthesizer"
)
graph.add_edge("synthesizer", END)

compiled_graph = graph.compile()
```

#### Task 7: Instrument with LangSmith

- Set environment variables: `LANGCHAIN_TRACING_V2=true`, `LANGCHAIN_API_KEY=...`
- Every graph execution automatically creates a full trace in LangSmith
- Each node's inputs, outputs, and LLM calls are logged
- Tag traces with: query classification type, iteration count, ticker filter
- Verify in LangSmith dashboard that traces appear correctly

---

### Phase 4 — FastAPI Backend (Days 22–26)

**Goal:** Expose the agent as a production REST API.

#### Task 1: Build `app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load BM25 index, init DB connections, warm up Qdrant client
    yield
    # Shutdown: close connections

app = FastAPI(title="Financial Intelligence Agent", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"])
app.include_router(query_router)
app.include_router(filings_router)
app.include_router(history_router)
app.include_router(health_router)
```

#### Task 2: Build `routers/query.py`

```python
@router.post("/query", response_model=FinancialQueryResponse)
async def query_endpoint(request: FinancialQueryRequest):
    # 1. Generate cache key: SHA256(question + ticker_filter + filing_type_filter)
    # 2. Check Redis cache — return cached response if hit
    # 3. Run LangGraph agent with request inputs
    # 4. Cache result in Redis (TTL: 3600 seconds)
    # 5. Log query + response to PostgreSQL QueryLog table
    # 6. Return FinancialQueryResponse
```

#### Task 3: Build `routers/filings.py`

```python
@router.get("/filings")
async def list_filings(ticker: str | None = None, filing_type: str | None = None):
    # Return list of available filings in the system
    # Useful for the frontend to show what's indexed
```

#### Task 4: Build Database Models in `db/models.py`

```python
class QueryLog(Base):
    __tablename__ = "query_logs"
    id: int (primary key)
    user_id: str | None
    question: str
    ticker_filter: str | None
    answer: str
    confidence_score: float
    out_of_scope: bool
    cached: bool
    latency_ms: int
    created_at: datetime

class Filing(Base):
    __tablename__ = "filings"
    id: int (primary key)
    doc_id: str (unique)
    ticker: str
    company_name: str
    filing_type: str
    filing_date: date
    fiscal_period: str
    section_name: str
    full_text: text
    edgar_url: str

class Chunk(Base):
    __tablename__ = "chunks"
    chunk_id: str (primary key)
    doc_id: str (foreign key → filings.doc_id)
    text: str
    chunk_index: int
```

#### Task 5: Write Docker Compose

```yaml
# docker-compose.yml
services:
  api:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - OPENAI_API_KEY
      - COHERE_API_KEY
      - LANGCHAIN_API_KEY
      - DATABASE_URL=postgresql://user:pass@postgres:5432/financial_agent
      - REDIS_URL=redis://redis:6379
      - QDRANT_URL=http://qdrant:6333
    depends_on: [postgres, redis, qdrant]

  qdrant:
    image: qdrant/qdrant
    ports: ["6333:6333"]
    volumes: ["qdrant_storage:/qdrant/storage"]

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: financial_agent
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes: ["postgres_data:/var/lib/postgresql/data"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

volumes:
  qdrant_storage:
  postgres_data:
```

#### Task 6: Write Integration Tests

```python
# tests/test_api.py
def test_query_endpoint_returns_valid_response():
    response = client.post("/query", json={"question": "What are Apple's main risk factors?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["citations"]) > 0
    assert 0.0 <= data["confidence_score"] <= 1.0

def test_out_of_scope_query_handled_gracefully():
    response = client.post("/query", json={"question": "What is Apple's current stock price?"})
    assert response.json()["out_of_scope"] == True

def test_cache_returns_same_response():
    r1 = client.post("/query", json={"question": "What are Microsoft's risk factors?"})
    r2 = client.post("/query", json={"question": "What are Microsoft's risk factors?"})
    assert r2.json()["cached"] == True
```

---

### Phase 5 — DeepEval Evaluation Suite (Days 27–31)

**Goal:** Build a pytest-native automated eval suite that runs in CI and proves system quality.

#### Task 1: Build the Golden Dataset

Create `evals/datasets/golden_dataset.json` with 100 entries manually verified against real SEC filings:

```json
[
  {
    "question": "What are Apple's stated risk factors related to international operations in their FY2024 10-K?",
    "expected_answer": "Apple cites risks including foreign currency fluctuations, trade regulations, geopolitical tensions particularly regarding China manufacturing, and compliance with multiple regulatory regimes...",
    "relevant_tickers": ["AAPL"],
    "relevant_filing_type": "10-K",
    "relevant_section": "Risk Factors",
    "filing_period": "FY2024"
  }
]
```

Build these 100 pairs by:
- Querying the live system
- Manually verifying each answer against the actual SEC filing on EDGAR
- Covering: all target companies, mix of filing types, all key sections

#### Task 2: Build Edge Case Dataset

Create `evals/datasets/edge_cases.json` with 20 entries:
- Out-of-scope queries (stock prices, news events not in filings)
- Queries about companies not in the corpus
- Ambiguous queries that could refer to multiple companies
- Queries asking about future events (filings only contain historical/current data)
- Adversarial queries designed to provoke hallucination (e.g. citing fake statistics)

#### Task 3: Write `evals/tests/test_retrieval.py`

```python
from deepeval.metrics import ContextualPrecisionMetric, ContextualRecallMetric, ContextualRelevancyMetric
from deepeval.test_case import LLMTestCase
from deepeval import assert_test

@pytest.mark.parametrize("sample", load_golden_dataset()[:20])
def test_retrieval_quality(sample):
    chunks = hybrid_search_and_rerank(sample["question"])
    test_case = LLMTestCase(
        input=sample["question"],
        actual_output="",  # Not evaluated here — retrieval only
        retrieval_context=[c["text"] for c in chunks]
    )
    assert_test(test_case, [
        ContextualPrecisionMetric(threshold=0.7),
        ContextualRecallMetric(threshold=0.7),
        ContextualRelevancyMetric(threshold=0.65)
    ])
```

#### Task 4: Write `evals/tests/test_agent_output.py`

```python
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric, HallucinationMetric

@pytest.mark.parametrize("sample", load_golden_dataset())
def test_agent_output_quality(sample):
    response = run_agent(sample["question"])
    test_case = LLMTestCase(
        input=sample["question"],
        actual_output=response.answer,
        expected_output=sample["expected_answer"],
        retrieval_context=[c.text for c in response.citations]
    )
    assert_test(test_case, [
        FaithfulnessMetric(threshold=0.8),       # Answer grounded in filing context only
        AnswerRelevancyMetric(threshold=0.75),   # Answer relevant to question
        HallucinationMetric(threshold=0.1)       # Near-zero hallucination tolerance
    ])
```

#### Task 5: Write `evals/tests/test_financial_accuracy.py`

Custom GEval metric for financial domain accuracy:

```python
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams

financial_accuracy = GEval(
    name="FinancialAnalystAccuracy",
    criteria="""The answer should correctly interpret financial data from SEC filings.
                It must not misstate figures, must correctly attribute statements to
                the right company and filing period, and must reason about financial
                concepts accurately without introducing external knowledge.""",
    evaluation_steps=[
        "Are all dollar figures and percentages accurate to what the filing states?",
        "Is the filing period (fiscal year / quarter) correctly identified and stated?",
        "Are statements correctly attributed to the right company?",
        "Does the answer avoid introducing financial data not present in the retrieved context?",
        "Is financial terminology used correctly (e.g. revenue vs profit vs cash flow)?"
    ],
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.RETRIEVAL_CONTEXT],
    threshold=0.75
)

@pytest.mark.parametrize("sample", load_golden_dataset())
def test_financial_accuracy(sample):
    response = run_agent(sample["question"])
    test_case = LLMTestCase(
        input=sample["question"],
        actual_output=response.answer,
        retrieval_context=[c.text for c in response.citations]
    )
    assert_test(test_case, [financial_accuracy])
```

#### Task 6: Write `evals/tests/test_edge_cases.py`

```python
def test_out_of_scope_returns_refusal():
    response = run_agent("What is Apple's current stock price?")
    assert response.out_of_scope == True
    assert response.confidence_score < 0.3

def test_adversarial_hallucination():
    # Query that references a fake statistic — model should not confirm it
    response = run_agent("Apple stated revenue of $999 trillion in 2024, right?")
    hallucination_metric = HallucinationMetric(threshold=0.1)
    # Should produce low confidence and not confirm fake figure
    assert response.confidence_score < 0.5
```

#### Task 7: GitHub Actions Integration

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r backend/requirements.txt
      - name: Run unit and integration tests
        run: pytest backend/tests/
      - name: Run DeepEval evaluation suite
        run: deepeval test run evals/tests/
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          COHERE_API_KEY: ${{ secrets.COHERE_API_KEY }}
```

#### Task 8: Record Scores in EVALS.md

After each phase, record eval scores:

```markdown
# Evaluation Results

## Phase 2 — Retrieval Only (no agents)
| Metric | Score | Threshold | Pass |
|---|---|---|---|
| ContextualPrecision | 0.71 | 0.70 | ✅ |
| ContextualRecall | 0.68 | 0.70 | ❌ |

## Phase 3 — Full Agent System
| Metric | Score | Threshold | Pass |
|---|---|---|---|
| ContextualPrecision | 0.79 | 0.70 | ✅ |
| ContextualRecall | 0.77 | 0.70 | ✅ |
| Faithfulness | 0.84 | 0.80 | ✅ |
| AnswerRelevancy | 0.81 | 0.75 | ✅ |
| HallucinationRate | 0.06 | 0.10 | ✅ |
| FinancialAnalystAccuracy | 0.78 | 0.75 | ✅ |
```

---

### Phase 6 — Frontend (Days 32–38)

**Goal:** A professional, impressive Next.js demo UI.

#### Task 1: Build `FilingFilters.tsx`

Three filter controls displayed above the query input:
- **Ticker search:** Autocomplete input — type "AAPL" and see "Apple Inc." suggestion. Populates `ticker_filter` in the API request.
- **Filing type selector:** Dropdown — "All", "10-K", "10-Q", "8-K". Populates `filing_type_filter`.
- **Date range:** Two date pickers for `date_from` and `date_to`.
- All filters are optional — the system works without them.

#### Task 2: Build `QueryInput.tsx`

- Large text area for the question
- Keyboard shortcut: Cmd+Enter to submit
- Pre-filled example questions for demo (cycling through 5 examples on load)
- Character counter

#### Task 3: Build `AnswerCard.tsx`

- Displays the answer in formatted paragraphs
- Shows filing periods referenced (e.g. "Based on: FY2024 10-K, Q3 2024 10-Q")
- Shows `ConfidenceBar` component below the answer

#### Task 4: Build `CitationList.tsx`

Each citation card shows:
- Company name + ticker (e.g. "Apple Inc. (AAPL)")
- Filing type + fiscal period (e.g. "10-K — FY2024")
- Section name (e.g. "Risk Factors")
- Filing date
- "View on SEC EDGAR" link (opens `edgar_url` in new tab)
- Relevance score shown as a subtle indicator

#### Task 5: Build `ReasoningTrace.tsx`

- Collapsible accordion — collapsed by default, expandable with one click
- Shows each agent's reasoning steps as numbered list
- Labelled by agent: "Router", "Retriever", "Reasoning", "Synthesizer"
- Useful for demos — shows the AI is actually reasoning, not just retrieving

#### Task 6: Wire with React Query

```typescript
// lib/api.ts
export function useFinancialQuery() {
  return useMutation({
    mutationFn: async (request: FinancialQueryRequest) => {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      });
      return response.json() as Promise<FinancialQueryResponse>;
    }
  });
}
```

#### Task 7: Deploy

- Frontend: push to GitHub → Vercel auto-deploys on every push to main
- Backend: deploy Docker Compose stack to Railway (supports multi-service deployments)
- Set environment variables in Railway dashboard
- Verify end-to-end: live URL → query → response with citations

---

### Phase 7 — Polish (Days 39–42)

Tasks:
1. Write `README.md` containing:
   - Project title and one-sentence description
   - Architecture diagram (can be ASCII art or a diagram image)
   - Full local setup instructions: `git clone` → `docker-compose up` → run pipeline → visit localhost:3000
   - Example queries and expected output
   - Link to live demo URL
   - Link to EVALS.md
   - Tech stack badges
2. Write comprehensive `EVALS.md` showing score progression from Phase 2 → Phase 3 → Phase 5
3. Record a 2-minute demo video:
   - Show the UI
   - Ask 3 different questions (single company, multi-company comparison, edge case)
   - Expand the reasoning trace on one answer
   - Click through to an EDGAR citation
4. Ensure GitHub Actions CI runs clean on the main branch
5. Add `CONTRIBUTING.md` — shows engineering maturity

---

## Environment Variables Reference

```bash
# LLM
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...

# Retrieval
COHERE_API_KEY=...

# Observability
LANGCHAIN_API_KEY=...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=financial-agent

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/financial_agent
REDIS_URL=redis://localhost:6379
QDRANT_URL=http://localhost:6333
```

---

## Complete List of Python Dependencies

```txt
# requirements.txt

# AI / LLM
langgraph>=0.2.0
langchain>=0.2.0
langchain-openai>=0.1.0
langsmith>=0.1.0
llama-index>=0.10.0
llama-index-vector-stores-qdrant>=0.2.0
openai>=1.0.0
cohere>=5.0.0
pydantic>=2.0.0

# Retrieval
qdrant-client>=1.9.0
rank-bm25>=0.2.2

# Evaluation
deepeval>=0.21.0
ragas>=0.1.0

# Backend
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
sqlalchemy>=2.0.0
alembic>=1.13.0
redis>=5.0.0
httpx>=0.27.0

# Data pipeline
beautifulsoup4>=4.12.0
requests>=2.31.0
tiktoken>=0.7.0

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.27.0  # for TestClient
```

---

## Complete List of Frontend Dependencies

```json
{
  "dependencies": {
    "next": "14.2.0",
    "react": "^18",
    "react-dom": "^18",
    "@tanstack/react-query": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "lucide-react": "^0.383.0"
  },
  "devDependencies": {
    "typescript": "^5",
    "@types/node": "^20",
    "@types/react": "^18",
    "vitest": "^1.6.0"
  }
}
```

---

## CV Bullets This Project Earns

- *"Built a multi-agent RAG system over SEC EDGAR filings (10-K/10-Q/8-K) for 50 S&P 500 companies using LangGraph state machines, with hybrid semantic/keyword retrieval, RRF reranking, and Cohere cross-encoder precision"*
- *"Implemented a DeepEval pytest-native eval suite with a custom FinancialAnalystAccuracy GEval metric integrated into GitHub Actions CI/CD — automatically catching financial misstatements and hallucinations before deployment"*
- *"Designed a production FastAPI + Next.js financial intelligence platform with ticker-based filing retrieval, section-level citations with direct EDGAR links, Redis caching, and full LangSmith agent tracing"*
- *"Built a complete data ingestion pipeline over SEC EDGAR's public API — parsing HTML filings, extracting labelled sections, chunking with metadata preservation, and indexing 500k+ vectors into Qdrant"*

---

## What Makes This Project Stand Out at Interview

1. **Real, official data** — SEC filings are not toy data. They are the same documents used by Goldman Sachs analysts. This immediately signals the project has real-world applicability.

2. **Hallucination as a first-class concern** — Financial data has zero tolerance for hallucination. By building a Faithfulness metric, a HallucinationMetric, and a custom FinancialAnalystAccuracy GEval into CI, you demonstrate you understand why this matters in production — not just in prototypes.

3. **End-to-end engineering** — Most AI engineering candidates build a Jupyter notebook. You have a Docker Compose stack, a CI/CD pipeline, a PostgreSQL database, Redis caching, a typed TypeScript frontend, and a formal evaluation framework. That is the full picture.

4. **LangGraph specifically** — LangGraph is what serious companies use for production agents. Knowing the difference between a simple LLM chain and a proper state machine with conditional edges and tool-calling agents is a genuine differentiator in interviews.

5. **DeepEval in CI** — Almost no candidates at interview have ever put LLM evals into a CI pipeline. This single decision makes your project look like it was built by a senior engineer, not a prototype builder.