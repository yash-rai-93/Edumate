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
from fastapi.staticfiles import StaticFiles  
from fastapi.responses import FileResponse
from typing import Optional
import datetime
import re
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="frontend"), name="static")

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
class PlanRequest(BaseModel):
    subject: str
    days: str
# --- HELPER: Calculate Exam Countdown ---
def get_exam_countdown():
    schedule_path = "data/exam_schedule/Schedule.txt"
    if not os.path.exists(schedule_path):
        return "Exam schedule file not found!"

    with open(schedule_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex to find dates like "February 17, 2026"
    # Adjust regex matches based on your Schedule.txt format
    today = datetime.date.today()
    response_text = "📅 **Exam Countdown:**\n"
    
    lines = content.split('\n')
    upcoming_exams = []

    for line in lines:
        if ":" in line and "2026" in line:  # Simple check for exam lines
            parts = line.split(":")
            subject = parts[0].strip()
            date_str = parts[1].strip()  # e.g., "Tuesday, February 17, 2026"
            
            try:
                # Parse date (Adjust format if needed)
                exam_date = datetime.datetime.strptime(date_str, "%A, %B %d, %Y").date()
                days_left = (exam_date - today).days
                
                if days_left >= 0:
                    upcoming_exams.append(f"• **{subject}**: {days_left} days left ({date_str})")
            except ValueError:
                continue

    if not upcoming_exams:
        return "No upcoming exams found in schedule or date format incorrect."
    
    return response_text + "\n".join(upcoming_exams)

# --- NEW ENDPOINTS ---

class TopicRequest(BaseModel):
    topic: str

@app.post("/quiz")
def generate_quiz(req: TopicRequest):
    return {"answer": rag.generate_quiz(req.topic)}

@app.post("/summary")
def get_summary(req: TopicRequest):
    return {"answer": rag.get_summary(req.topic)}

@app.get("/countdown")
def countdown():
    return {"answer": get_exam_countdown()}

@app.post("/mindmap")
def generate_mindmap(req: TopicRequest):
    return {"answer": rag.generate_mindmap(req.topic)}

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

@app.post("/study_plan")
def study_plan(req: PlanRequest):
    return {"answer": rag.generate_study_plan(req.subject, req.days)}

@app.get("/health")
def health_check():
    return {"message": "EduMate RAG Bot is running!"}
@app.get("/")
def read_root():
    return FileResponse("frontend/index.html")
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)