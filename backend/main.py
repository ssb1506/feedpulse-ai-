"""
FeedPulse AI — Main FastAPI Application
REST endpoints + WebSocket for live streaming + AI agent chat
"""

import asyncio
import json
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from simulator import PostSimulator
from consumer import PostConsumer
from agent import FeedPulseAgent


# ── WebSocket connection manager ─────────────────────────────────────────────

class ConnectionManager:
    """Manages active WebSocket connections for live post streaming."""

    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, data: dict):
        disconnected = []
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.active.remove(ws)


ws_manager = ConnectionManager()
loop = None  # Will be set to the running event loop


def on_post_callback(post: dict):
    """Called by consumer when a new post is processed. Broadcasts via WebSocket."""
    global loop
    if loop and ws_manager.active:
        asyncio.run_coroutine_threadsafe(ws_manager.broadcast(post), loop)


# ── App lifecycle ─────────────────────────────────────────────────────────────

simulator = PostSimulator()
consumer = PostConsumer(on_post=on_post_callback)
agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start simulator + consumer on app startup, stop on shutdown."""
    global loop, agent

    loop = asyncio.get_event_loop()

    # Start Kafka producer (generates fake posts)
    simulator.start()

    # Start Kafka consumer (processes posts)
    consumer.start()

    # Initialize AI agent (needs consumer's stores)
    agent = FeedPulseAgent(
        vector_store=consumer.vectors,
        iceberg_store=consumer.iceberg,
        consumer=consumer,
    )

    print("[App] FeedPulse AI is running!")
    yield

    simulator.stop()
    consumer.stop()
    print("[App] Shut down.")


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="FeedPulse AI",
    description="Real-time social media analytics with AI assistant",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── REST Endpoints ────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "running", "app": "FeedPulse AI"}


@app.get("/api/posts/recent")
def get_recent_posts(limit: int = 20):
    """Get most recent processed posts from memory."""
    posts = consumer.recent_posts[-limit:]
    posts.reverse()  # newest first
    return {"posts": posts, "count": len(posts)}


@app.get("/api/trending")
def get_trending(top_n: int = 10):
    """Get current trending topics."""
    return {"trending": consumer.get_trending(top_n)}


@app.get("/api/sentiment")
def get_sentiment():
    """Get current sentiment distribution."""
    return consumer.get_sentiment_summary()


@app.get("/api/sentiment/history")
def get_sentiment_history(hours: int = 6):
    """Get sentiment over time from Iceberg lakehouse."""
    return {"data": consumer.iceberg.get_sentiment_over_time(hours)}


@app.get("/api/stats")
def get_stats():
    """Get system stats."""
    return {
        "posts_processed": len(consumer.recent_posts),
        "vectors_stored": consumer.vectors.get_count(),
        "iceberg_snapshots": consumer.iceberg.get_snapshot_count(),
        "trending_words_tracked": len(consumer.trending_counts),
        "websocket_clients": len(ws_manager.active),
    }


class ChatRequest(BaseModel):
    message: str


@app.post("/api/chat")
async def chat_with_agent(req: ChatRequest):
    """Chat with the AI agent."""
    if agent is None:
        return {"response": "Agent not initialized yet. Please wait a moment."}

    response = await agent.chat(req.message)
    return {"response": response}


# ── WebSocket — Live post stream ──────────────────────────────────────────────

@app.websocket("/ws/feed")
async def websocket_feed(ws: WebSocket):
    """WebSocket endpoint — streams processed posts in real-time."""
    await ws_manager.connect(ws)
    try:
        while True:
            # Keep connection alive, listen for any client messages
            data = await ws.receive_text()
            # Client can send "ping" to keep alive
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
