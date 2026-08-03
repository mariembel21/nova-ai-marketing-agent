from __future__ import annotations

from fastapi import FastAPI
from dotenv import load_dotenv

# Load .env into environment (so GROQ_API_KEY and LLM_PROVIDER are available)
load_dotenv()

from backend.routes.content import router as content_router
from backend.routes.bio import router as bio_router
from backend.routes.presentation import router as presentation_router
from backend.routes.strategy import router as strategy_router
from backend.routes.social import router as social_router


app = FastAPI(title="Nova AI Marketing Agent", version="0.1.0")

app.include_router(content_router)
app.include_router(bio_router)
app.include_router(presentation_router)
app.include_router(strategy_router)
app.include_router(social_router)


@app.get("/health", tags=["system"])
def health_check() -> dict:
	return {"status": "ok"}
