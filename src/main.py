import asyncio

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from src.api.main import api_router
from src.database import init_db

app = FastAPI(debug=True)

app.include_router(api_router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://greater-grace-bundles.onrender.com"],  # Only your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# asyncio.run(init_db())
