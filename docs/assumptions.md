# Project Assumptions - ZeroDay PS2

## Architectural Decisions
- **Local OCR:** Using `pytesseract` or `pdfplumber` for local PDF extraction to avoid cloud OCR APIs.
- **Vector Store:** Using `ChromaDB` or `FAISS` in local-only mode for retrieval.
- **LLM Serving:** Assuming Ollama is installed on the host machine and accessible at `http://127.0.0.1:11434`.
- **Next.js Version:** Using Next.js 14+ with App Router and TypeScript.
- **State Management:** LangGraph's built-in state management used for the orchestration loop.

## Constraints Implementation
- **Privacy:** `NEXT_TELEMETRY_DISABLED=1` will be set in the `.env` of the web app. 
- **Tracing:** LangChain tracing will be disabled via `LANGCHAIN_TRACING_V2=false`.
- **Fonts:** Only system sans-serif fonts used in Tailwind config to avoid Google Fonts requests.
