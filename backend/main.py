from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Uvozimo rutere
from api.chat import router as chat_router
from api.auth import router as auth_router

app = FastAPI(title="Modularni RAG Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uključujemo rute pod api prefiksom
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(chat_router, prefix="/api", tags=["Chat"])

@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok", "poruka": "Modularni FastAPI RAG sistem je aktivan!"}