# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**pdf_chat** is a Streamlit-based web application that implements a Retrieval-Augmented Generation (RAG) chatbot for PDFs. Users can upload PDF documents, and the application extracts text, creates vector embeddings, stores them in a local Qdrant vector database, and allows users to ask questions that are answered using Claude LLM with retrieved context from their documents.

## Architecture

### High-Level Flow

1. **PDF Upload & Ingestion** (`page_pdf_upload_and_build_vector_db`)
   - User uploads PDF file via Streamlit uploader
   - Extract text using pypdf library
   - Split text into chunks (1000 chars, 100 char overlap) using LangChain's `RecursiveCharacterTextSplitter`
   - Generate embeddings using Voyage AI embeddings API (`voyage-4-lite` model)
   - Store vectors in local Qdrant database

2. **Query Processing** (`page_ask_my_pdf`)
   - User submits query via Streamlit text input
   - Query is embedded using the same Voyage AI model
   - Qdrant retrieves top-k similar chunks (k=10) using cosine similarity
   - LangChain's `RetrievalQA` orchestrates the flow using Claude LLM
   - Answer is displayed in the UI

### Key Components

- **Qdrant Vector Store** (`load_qdrant`)
  - Local persistence at `./local_qdrant`
  - Single collection: `my_collection` with 1024-dimensional vectors
  - Auto-creates collection on first run

- **Model Selection** (`select_model`)
  - User selects between Claude Haiku 4.5 (faster/cheaper) or Claude Sonnet 4.5 (more capable)
  - Sidebar radio button for selection

- **Rate Limit Handling** (`build_vector_store`)
  - Voyage AI free tier: 3 requests per minute (3 RPM)
  - Implements retry logic with exponential backoff (20s, 40s, 60s, 80s, 100s)
  - 21-second delay between embeddings to stay within limits
  - Graceful error handling: logs and skips chunks that fail after 5 retries

### Data Flow

```
PDF File Upload
    ↓
Extract Text (pypdf)
    ↓
Split into Chunks (1000 char windows)
    ↓
Count Tokens (logging only)
    ↓
Generate Embeddings (Voyage AI, with rate limiting)
    ↓
Store in Qdrant (vector DB)
    ↓
User Query
    ↓
Embed Query (Voyage AI)
    ↓
Retrieve Similar Chunks (Qdrant similarity search)
    ↓
Build Prompt with Retrieved Context
    ↓
Send to Claude LLM
    ↓
Display Answer
```

## Development Commands

### Setup & Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or with Docker
docker-compose up --build
```

### Running the Application

```bash
# Direct Streamlit run
streamlit run src/main.py

# Docker container
docker-compose up
# App will be available at http://localhost:8501
```

### Environment Variables

Create a `.env` file with:
```
ANTHROPIC_API_KEY=sk-ant-...
VOYAGE_API_KEY=pa-...
```

## Key Files

- **`src/main.py`** — Single entry point containing all application logic
  - Page initialization and routing
  - PDF processing and vectorization
  - QA chain setup and execution

- **`requirements.txt`** — Python dependencies (LangChain, Streamlit, Qdrant, Anthropic, VoyageAI)

- **`dockerfile`** — Docker image definition (Python 3.11 + Streamlit)

- **`docker-compose.yml`** — Service orchestration with volume mounting and port mapping (8501)

- **`local_qdrant/`** — Qdrant vector database persistence directory (created at runtime)

## Important Implementation Details

### Embedding Model
- Model: `voyage-4-lite` (lightweight, 1024 dimensions)
- Used for both PDF chunks and user queries
- Token counting available via `vo.count_tokens()` for monitoring

### Chunk Configuration
- Size: 1000 characters per chunk
- Overlap: 100 characters (ensures context continuity)
- Configurable via `RecursiveCharacterTextSplitter` parameters

### Retrieval Strategy
- Similarity search type: "similarity" (cosine distance)
- Top-k retrieval: k=10 (retrieve 10 most similar chunks per query)
- Vector distance metric: COSINE

### UI Patterns
- Two-page app via sidebar radio: "PDF Upload" and "Ask My PDF(s)"
- Progress bar + status text for embedding process
- Live error messages for rate limit or embedding failures
- Model selection dropdown in sidebar

## Common Debugging

**Rate Limit Errors**: Normal for Voyage AI free tier. The app handles them with backoff retry logic. Check logs for "レート制限発生" messages.

**Missing Collections**: Qdrant collection auto-creates on first run if it doesn't exist. Check `./local_qdrant/meta.json` exists.

**Embedding Failures**: If a chunk fails after 5 retries, it's skipped and logged. User will see an error message in the UI.

**API Key Issues**: Ensure `.env` file has both `ANTHROPIC_API_KEY` and `VOYAGE_API_KEY` set correctly.

## Japanese Comments in Code

The codebase contains Japanese comments and log messages. Key terms:
- **埋め込み** = embedding/vectorization
- **レート制限** = rate limit
- **トークン** = tokens
- **チャンク** = chunk
