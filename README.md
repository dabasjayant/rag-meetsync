# MeetSync - Retrieval-Augmented Generation (RAG) Pipeline for Project Management

**MeetSync** is an AI-powered project assistant with dynamic contextual updates for engineering & product teams

## Core Idea

**Problem:**
Teams often lose track of context and decisions scattered across meeting transcripts, Slack threads, and docs.  
Knowledge becomes siloed, fragmented, and stale, making it hard to find what was decided, when, and why.

**Solution:** 
MeetSync - an AI-powered progress aware assistant:
- Ingests PDFs, `.txt`, and `.md` files as knowledge sources.
- Extracts and chunks text intelligently.
- Embeds content with the **Mistral API**.
- Enables semantic + lexical retrieval through a **custom lightweight vector database**.
- Generates grounded answers with citations via LLM (Mistral-small).
- Includes a simple **web UI** for uploading files, managing memory, and chatting with the system.

## Contents
1. [Core Idea](#core-idea)
2. [Objective](#objective)
3. [Architecture](#architecture)
4. [Features](#features)
5. [Project Structure](#project-structure)
3. [Setup Instructions](#setup-instructions)
6. [Using the App](#using-the-app)
7. [Security and Reliability](#security-and-reliability)
8. [Key Design Decisions](#key-design-decisions)
9. [Example Query Flow](#example-query-flow)
10. [Bonus Features](#bonus-features)
11. [Author](#author)
12. [Summary](#summary)

## Objective

Enable project teams to interact with a dynamically updated, centralized knowledge base that integrates meeting transcripts, project documents, and chat-based UI to instantly retrieve the latest insights and decisions.

![meetsync-ui](previews/landing_page.png "meetsync-ui")
![meetsync-chat-ui](previews/chat_ui.png "meetsync-chat-ui")

## Architecture

| Layer | Components | Description |
|-------|-------------|-------------|
| **Frontend (UI)** | `index.html`, `js/`, `css/` | Simple static interface for uploading files, querying the system, and managing files. |
| **Backend (FastAPI)** | `app/main.py`, `routes/*.py` | REST API for ingestion, query, and deletion. CORS-enabled, serves UI statically. |
| **Ingestion Layer** | `core/ingest_pipeline.py` | Extracts text from `.pdf`, `.txt`, `.md`, chunks, embeds, and stores locally. |
| **Retrieval Layer** | `core/query_pipeline.py` | Hybrid (semantic + keyword) retrieval over local embeddings and text chunks. |
| **Generation Layer** | `core/generation.py` | Builds prompt, calls Mistral chat model, generates structured, citation-backed answer. |
| **Policy Layer** | `core/policy.py` | Rejects PII, legal, or medical queries for safety. |
| **Resilience Layer** | `core/utils.py` | Implements exponential backoff retry for rate-limited (429) API calls. |
| **Data Storage** | `/data/` | Stores `chunks.jsonl`, `metadata.jsonl`, and `embeddings.npy` locally. |
| **Config** | `config.py`, `.env` | Centralized model & API settings. |
| **Launcher** | `launch.py` | Starts Uvicorn with reloading for local dev. |

---

## Features

| Capability | Description |
|-------------|-------------|
| **Multi-format ingestion** | Upload `.pdf`, `.txt`, `.md` project docs or meeting transcripts. |
| **Local vector store** | NumPy + JSON-based index for embeddings (no external DB). |
| **Hybrid retrieval** | Combines cosine similarity and keyword overlap. |
| **Adaptive generation** | Uses prompt templates for lists, tables, and paragraph styles. |
| **Citation-based output** | LLM responses cite chunk IDs for traceability. |
| **Evidence thresholding** | Refuses answers when top chunks have low similarity. |
| **Hallucination filter** | Scans answers for unsupported content. |
| **Query refusal policies** | Detects and rejects PII, legal, or medical queries. |
| **Rate-limit handling** | Retry with exponential backoff and jitter for Mistral API. |
| **File management** | List, delete, and reset ingested files dynamically. |

---

## Project Structure

```
rag-meetsync/
│
├── app/
│ ├── main.py # FastAPI entrypoint
│ ├── config.py # Loads environment and runtime config
│ ├── models.py # Pydantic schemas
│ │
│ ├── core/
│ │ ├── ingest_pipeline.py # File ingestion, text extraction, embeddings
│ │ ├── query_pipeline.py # Semantic + keyword search and ranking
│ │ ├── generation.py # LLM-based answer generation with citations
│ │ ├── policy.py # PII, legal, and medical query refusal
│ │ ├── utils.py # Retry & backoff for API rate limits
│ │ └── init.py
│ │
│ ├── routes/
│ │ ├── ingest.py # POST /ingest - upload files
│ │ ├── query.py # POST /query - ask questions
│ │ ├── files.py # GET /files - list files
│ │ ├── delete.py # DELETE /delete/{file_id} or /all
│ │ └── init.py
│ │
│ └── ui/ # Static frontend
│ ├── index.html
│ ├── js/
│ └── css/
│
├── data/ # Local knowledge base storage
│ ├── chunks.jsonl
│ ├── metadata.jsonl
│ └── embeddings.npy
│
├── launch.py # Starts the FastAPI server
├── .env # Environment variables
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### Clone and Install
```bash
git clone https://github.com/dabasjayant/rag-meetsync.git
cd rag-meetsync
pip install -r requirements.txt
```

### Environment Setup
Create a `.env` file at project root:
```
MISTRAL_API_KEY=your_api_key_here
MISTRAL_EMBED_MODEL=mistral-embed
MISTRAL_CHAT_MODEL=mistral-small
HOST=127.0.0.1
PORT=8000
DATA_DIR=data
```

### Run the App
```
python launch.py
```

App will start at: http://127.0.0.1:8000


## Using the App

### Upload Files
- Go to the web UI and click "+" icon.
- Supportes `.pdf`, `.txt`, and `.md` file formats.
- The system extracts text, chunks it (~500 chars per chunk), and embeds via Mistral API.

### Manage Knowledge Base

| Endpoint            | Description                                                      |
| ------------------- | ---------------------------------------------------------------- |
| `/files`            | Lists all ingested files with IDs, timestamps, and chunk counts. |
| `/delete/{file_id}` | Deletes a specific file and its embeddings.                      |
| `/delete/all`       | Clears the entire knowledge base.                                |


### Querying
- Enter natural language questions in the chat box.
- The pipeline:
  1. Detects intent (skip greetings).
  2. Filters for PII/legal/medical content.
  3. Performs hybrid retrieval (semantic + keyword).
  4. Generates a grounded answer using Mistral Chat with chunk citations.
  5. Filters hallucinations or low-evidence answers.

## Security and Reliability

| Concern                       | Mitigation                                              |
| ----------------------------- | ------------------------------------------------------- |
| **Rate limits (429)**         | Automatic exponential backoff with jitter in `utils.py` |
| **PII/Legal/Medical queries** | Refused with clear message in `policy.py`               |
| **Fault tolerance**           | Defensive checks for empty or missing files             |
| **Data privacy**              | All embeddings and texts stored locally only            |
| **CORS/Frontend safety**      | Enabled in FastAPI middleware; inputs sanitized         |

## Key Design Decisions

| Decision                         | Rationale                                                |
| -------------------------------- | -------------------------------------------------------- |
| **No external vector DB**        | Complies with task requirement; transparent, portable    |
| **FastAPI**                      | Modern async Python framework with static serving        |
| **Mistral API**                  | Unified provider for both embeddings and LLM completions |
| **Local file-backed storage**    | Easy to inspect and reset between runs                   |
| **Chunking by character length** | Balances embedding quality and latency                   |
| **PII/Legal filter**             | Demonstrates responsible AI practice                     |
| **Retry logic for rate limits**  | Avoids crashing on API 429 errors                        |
| **UUID-based file IDs**          | Prevents collisions for same filenames                   |

## Example Query Flow

### User Input:
> "List the key decisions made in the last sprint review."

### Pipeline Flow:
1. Intent Detection: Query is informational → triggers search.
2. Retrieval: Hybrid search ranks top-k chunks by similarity + keyword overlap.
3. Evidence Thresholding: Ensures top results exceed similarity cutoff.
4. Prompt Construction: Chunks formatted as [0] ... [n] for LLM grounding.
5. Generation: Mistral Chat model generates an answer with citations.
6. Post-Processing: Citations extracted; hallucinations flagged.

### Sample Response:
- The team finalized the API versioning strategy [0]
- The backend migration to EC2 was postponed [2]

Sources:
- project-kickoff-meeting-8f2a12e3a1:chunk_05
- project-kickoff-meeting-8f2a12e3a1:chunk_06

## Bonus Features

- Citations with thresholds: Refuses to answer when evidence is weak
- Adaptive prompt templates: Paragraph, list, or table formatting
- Hallucination filter: Detects unsupported claims
- Query refusal policy: Rejects PII, legal, or medical content
- Exponential backoff: Handles Mistral 429 errors gracefully
- Dynamic file management: Ingest, list, delete, or reset knowledge base anytime

## Author

**Jayant Dabas**<br>
Machine Learning Engineer | Data Scientist<br>
GitHub: [@JayantDabas](https://github.com/dabasjayant)

## Summary

MeetSync demonstrates a clean, production-style implementation of a Retrieval-Augmented Generation pipeline:

- Full FastAPI backend with modular components
- Mistral API integration for both embeddings and generation
- No third-party RAG or vector DBs
- Responsible AI practices (PII filter, evidence thresholds)
- Simple and interactive web UI

It serves as a practical, well-structured demonstration of applied AI engineering and full-stack RAG design.