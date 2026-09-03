from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv()
from fastapi.middleware.cors import CORSMiddleware

from app.routers import upload
from app.routers import chat
from app.routers import analyze
from app.routers import feature_engineering

app = FastAPI(
    title="AI Data Scientist Platform",
    description="Upload any dataset, chat with it, get analysis and predictions.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
app.include_router(feature_engineering.router, prefix="/api/v1")
app.include_router(chat.router)
app.include_router(analyze.router)


@app.get("/")
def health_check():
    return {"status": "ok", "message": "AI Data Scientist backend running"}