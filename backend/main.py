from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="AI Customer Support Copilot")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []

class ChatResponse(BaseModel):
    answer: str
    sentiment: str
    escalate: bool
    context_used: List[str]

@app.get("/")
async def root():
    return {"message": "AI Customer Support Copilot API is running"}

from rag_engine import RAGEngine
from utils import analyze_sentiment, detect_escalation

# Initialize RAG Engine
# Note: Ensure OPENAI_API_KEY is set in environment
rag = None
try:
    rag = RAGEngine()
except Exception as e:
    print(f"RAG Engine initialization failed (likely missing API key): {e}")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not rag:
        raise HTTPException(status_code=500, detail="RAG Engine not initialized. Check API Key.")
    
    # Analyze user sentiment
    sentiment = analyze_sentiment(request.message)
    
    # Detect escalation
    escalate = detect_escalation(request.message, sentiment)
    
    # Format chat history for LangChain
    formatted_history = []
    for msg in request.history:
        formatted_history.append((msg.role, msg.content))
    
    # Query RAG Engine
    try:
        rag_result = rag.query(request.message, chat_history=formatted_history)
        
        return ChatResponse(
            answer=rag_result["answer"],
            sentiment=sentiment,
            escalate=escalate,
            context_used=rag_result["source_documents"]
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest")
async def ingest_data(file: UploadFile = File(...)):
    if not rag:
        raise HTTPException(status_code=500, detail="RAG Engine not initialized.")
    
    # Save file temporarily
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())
    
    try:
        rag.ingest_document(temp_path)
        os.remove(temp_path)
        return {"filename": file.filename, "status": "success"}
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
