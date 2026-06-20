import os
import threading
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from backend.detector import AntiScamDetector
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Jagain API", description="Anti-Scam Analysis Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MessageRequest(BaseModel):
    message: str
    
# Lazy load detector
detector = None
detector_lock = threading.Lock()

@app.get("/api/status")
def get_status():
    global detector
    db_status = os.path.exists("scam_urls.db")
    azure_status = all([
        os.getenv("AZURE_OPENAI_API_KEY"),
        os.getenv("AZURE_SEARCH_API_KEY")
    ])
    return {
        "status": "healthy",
        "sqlite_loaded": db_status,
        "azure_configured": azure_status
    }

@app.post("/api/check-message")
def check_message(req: MessageRequest):
    global detector
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    if detector is None:
        with detector_lock:
            if detector is None:
                try:
                    detector = AntiScamDetector()
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Failed to initialize Azure clients: {e}")
            
    try:
        result = detector.analyze_message(req.message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
# Mount static files to serve the frontend
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
