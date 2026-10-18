from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from services.api.app.config.settings import settings
from services.api.app.orchestrator.graph import legal_graph
from services.api.app.services.ingestion import ingestion_service
import shutil
import os
import uuid

app = FastAPI(title=settings.APP_NAME)

# Privacy: Strict CORS for local-only operation
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": settings.OLLAMA_MODEL}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    doc_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}{os.path.splitext(file.filename)[1]}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Pre-run ingestion to verify it's a legal doc
    try:
        text = ingestion_service.extract_text(file_path)
        # Basic check for non-legal files can be added here
    except Exception as e:
        return {"error": f"Failed to process file: {str(e)}"}, 400

    return {"doc_id": doc_id, "filename": file.filename}

@app.post("/chat")
async def chat(doc_id: str = Form(...), query: str = Form(...)):
    # Path to the uploaded file
    # In a real app, we'd store the path in a DB
    file_exts = ['.pdf', '.txt']
    found_path = None
    for ext in file_exts:
        path = os.path.join(UPLOAD_DIR, f"{doc_id}{ext}")
        if os.path.exists(path):
            found_path = path
            break

    if not found_path:
        return {"error": "Document not found"}, 404

    inputs = {
        "doc_id": found_path,
        "user_query": query,
        "is_legal_doc": False
    }

    result = legal_graph.invoke(inputs)

    if not result.get("is_legal_doc"):
        return {"response": "This document does not appear to be a legal document and cannot be processed."}

    return {"response": result.get("final_response", "No analysis could be generated.")}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.BIND_ADDRESS, port=settings.BIND_PORT)
