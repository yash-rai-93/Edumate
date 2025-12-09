from fastapi import FastAPI, Response
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
