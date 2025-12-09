"""from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag_pipeline import EduMateRAG

app = FastAPI()

# ---------------------------
# ENABLE CORS FOR FRONTEND 
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # allow all origins
    allow_credentials=True,
    allow_methods=["*"],      # allow POST, GET, OPTIONS
    allow_headers=["*"],      # allow JSON headers
)

rag = EduMateRAG()

class Query(BaseModel):
    question: str

# Required for browser preflight check
@app.options("/ask")
def options_handler():
    return Response(status_code=200)

@app.post("/ask")
def ask(query: Query):
    answer = rag.ask(query.question)
    
    # If LangChain returns an LLMResult-like object → extract .content
    if hasattr(answer, "content"):
        answer = answer.content

    return {"answer": answer}

@app.get("/")
def root():
    return {"message": "EduMate RAG Bot is running!"}
"""""
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag_pipeline import EduMateRAG
import uvicorn
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag = EduMateRAG()

# Global dictionary to store chat history
# Format: { "session_id_123": [("Hi", "Hello"), ("Q2", "A2")] }
sessions = {}

class Query(BaseModel):
    question: str
    session_id: str  # <--- New Field

@app.post("/ask")
def ask(query: Query):
    # Get history for this user (or create empty list if new)
    user_history = sessions.get(query.session_id, [])
    
    # Pass history to RAG
    answer = rag.ask(query.question, chat_history=user_history)
    
    # Save the new interaction to history
    user_history.append((query.question, answer))
    
    # Keep only last 5 exchanges to save memory/speed
    if len(user_history) > 5:
        user_history.pop(0)
        
    sessions[query.session_id] = user_history

    return {"answer": answer}

@app.get("/")
def root():
    return {"message": "EduMate RAG Bot is running!"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)