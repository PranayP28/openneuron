# ZeroDay PS2: Project Implementation Procedure

## 🚀 Project Overview
ZeroDay PS2 is a private, on-device legal document triage agent. It is designed to process legal documents locally using a Compound AI System architecture, ensuring that no sensitive data ever leaves the user's machine.

## 🛠️ Technical Architecture
The system follows a multi-layered approach:
1. **Ingestion Layer**: Local PDF/TXT extraction and context-aware chunking.
2. **Retrieval Layer**: Hybrid local search using ChromaDB for precise context fetching.
3. **Orchestration Layer**: A LangGraph state machine that routes queries, runs parallel analysis, and merges results.
4. **Verification Layer**: A grounding service that ensures every AI claim is backed by evidence in the text.
5. **Safety Layer**: A policy filter that blocks the AI from giving legal verdicts or advice.
6. **Observability Layer**: SQLite-based metrics and JSON manifests for complete reproducibility.

## 📝 Step-by-Step Implementation Procedure

### Phase 1: Foundation & Setup
- **Monorepo Initialization**: Set up the project structure with separate `apps/app` and `services/api`.
- **Environment Configuration**: Created `scripts/setup.sh` to handle the installation of Ollama, Python dependencies (`services/api/requirements.txt`), and the Gemma model (`gemma3:4b` by default, override with `OLLAMA_MODEL`).
- **Strict Privacy Settings**: Configured the system to bind to `127.0.0.1` and disabled all cloud telemetry (`NEXT_TELEMETRY_DISABLED=1`).
- **Config Management**: Implemented a Pydantic-based settings system for reproducibility (Fixed seed, Temp 0).

### Phase 2: Ingestion & Basic Inference
- **Local Extraction**: Built the `IngestionService` to handle PDF and TXT files locally.
- **Smart Chunking**: Implemented a sliding-window chunker to maintain context across segments.
- **Inference Wrapper**: Created an `InferenceClient` for Ollama, including a `MockInferenceClient` for deterministic unit testing.
- **Prompt Engineering**: Developed versioned templates for classification and analysis with few-shot examples.

### Phase 3: RAG & Orchestration
- **Vector Store**: Integrated ChromaDB for local embedding storage and cosine similarity retrieval.
- **State Machine**: Designed the LangGraph orchestrator.
    - **Routing**: Implemented a classifier node to reject non-legal documents.
    - **Parallel Analysis**: Created a fan-out pattern to analyze Clauses, Risks, Obligations, and Deadlines concurrently.
- **Integration**: Connected retrieval to analysis to ensure the model only sees relevant document fragments.

### Phase 4: Verification & Safety
- **Evidence Grounding**: Built the `VerificationService` to prevent hallucinations by checking claims against the original text.
- **Safety Guardrails**: Implemented `SafetyService` to scan and block forbidden terms like "illegal" or "you will win".
- **Local Observability**: Added SQLite metrics for performance tracking and JSON manifests for auditability.

### Phase 5: Frontend Integration
- **API Development**: Created FastAPI endpoints for `/upload`, `/chat` and `/chat/stream` (NDJSON; streams each analysis section as soon as it is ready).
- **UI Development**: Built a Next.js chat interface with Tailwind CSS.
- **Privacy Polish**: Removed all external CDNs and Google Fonts, using system-native fonts only.

## 🚀 How to Run the Project

1. **Install Ollama**: Download from ollama.com.
2. **Run Setup**:
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```
3. **Start Backend** (from the repo root):
   ```bash
   source venv/bin/activate
   python services/api/main.py
   ```
   Optional, for lower latency: start Ollama with `OLLAMA_NUM_PARALLEL=4 ollama serve` and set `LLM_MAX_PARALLEL=4` in `.env` so the four analyses run concurrently on the model too. The default (`LLM_MAX_PARALLEL=1`) queues model calls in the API so they don't time out behind a single Ollama slot.
4. **Start Frontend**:
   ```bash
   cd apps/app
   npm install
   npm run dev
   ```
   Set `NEXT_PUBLIC_API_URL` if the backend is not on `http://127.0.0.1:8000`.
5. **Run Tests** (from the repo root): `python -m pytest`
6. **Use**: Upload a PDF/TXT and start asking legal triage questions.

## 🛡️ Privacy & Compliance Verification
- [x] All traffic stays on `127.0.0.1`.
- [x] No cloud LLM calls.
- [x] No telemetry or remote fonts.
- [x] All claims verified against source text.
- [x] No legal verdicts provided.
