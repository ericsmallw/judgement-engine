import time
from contextlib import asynccontextmanager
from dataclasses import asdict

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app import db
from app.gate import run_gate


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db()
    app.state.http = httpx.AsyncClient()
    yield
    await app.state.http.aclose()


app = FastAPI(title="Judgment Engine", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"]
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


@app.post("/chat")
async def chat(req: ChatRequest):
    start = time.perf_counter()
    try:
        result = await run_gate(req.message, app.state.http)
    except httpx.HTTPError as exc:
        print(f"GATE FAILURE: {exc!r}")   # temporary: shows the URL and cause
        raise HTTPException(503, "The safety gate is unavailable, so the message was not sent anywhere.")
    
    latency_ms = int((time.perf_counter() - start) * 1000)
    await db.log_decision(result, latency_ms)
    return {**asdict(result), "latency_ms": latency_ms}


@app.get("/decisions")
async def decisions():
    return await db.recent()


@app.get("/health")
async def health():
    return {"status": "ok"}