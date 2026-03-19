# FeedPulse AI 🔴

**Real-time social media analytics platform with AI-powered insights**

FeedPulse AI streams social media posts through Apache Kafka, analyzes sentiment and trending topics in real-time, stores everything in an Apache Iceberg lakehouse for time-travel analytics, and provides an AI assistant (LangChain + Gemini) that can search posts and query historical trends through natural conversation.

![Tech Stack](https://img.shields.io/badge/Kafka-Streaming-teal)
![Tech Stack](https://img.shields.io/badge/Iceberg-Lakehouse-blue)
![Tech Stack](https://img.shields.io/badge/LangChain-AI_Agent-purple)
![Tech Stack](https://img.shields.io/badge/React-Frontend-orange)
![Tech Stack](https://img.shields.io/badge/FastAPI-Backend-green)

---

## What It Does

1. **Posts stream in** — A simulator generates realistic social media posts every 1-2 seconds
2. **Kafka delivers them** — Posts flow through Kafka topics, managed by ZooKeeper
3. **Processing happens** — Each post gets sentiment analysis, keyword extraction, and vector embedding
4. **Iceberg stores history** — All posts land in an Iceberg lakehouse with time-travel capability
5. **Dashboard shows it live** — React frontend with WebSocket shows real-time feed, charts, and trends
6. **AI answers questions** — Ask the LangChain agent "What's trending?" or "Why did sentiment drop?"

---

## Tech Stack

### Frontend
- **React 18** — UI framework
- **Recharts** — Live sentiment charts and pie charts
- **WebSocket** — Real-time post streaming (no page refresh)
- **Tailwind CSS** — Styling
- **Vite** — Build tool
- **Lucide React** — Icons

### Backend
- **FastAPI** (Python) — REST API + WebSocket server
- **LangChain** — AI agent orchestration with ReAct pattern
- **Google Gemini 2.0 Flash** — LLM for the AI assistant
- **FAISS** — In-memory vector store for semantic search (RAG)
- **Sentence-Transformers** — Embedding generation (`all-MiniLM-L6-v2`)
- **TextBlob** — Sentiment analysis

### Streaming & Storage
- **Apache Kafka** — Event streaming (posts flow as real-time events)
- **Apache ZooKeeper** — Kafka broker coordination
- **Apache Iceberg** (PyIceberg) — Lakehouse table format with time-travel queries
- **PyArrow + Parquet** — Columnar storage format under Iceberg

### Infrastructure
- **Docker Compose** — Single command runs everything
- **Python 3.11** / **Node.js 18**

---

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- (Optional) Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

### Run

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/feedpulse-ai.git
cd feedpulse-ai

# Set your API key (optional — works without it in fallback mode)
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Start everything
docker-compose up --build

# Open in browser
# Dashboard: http://localhost:3000
# API docs: http://localhost:8000/docs
```

### Without Docker (development)

```bash
# Terminal 1 — Start Kafka + ZooKeeper
docker-compose up zookeeper kafka

# Terminal 2 — Backend
cd backend
pip install -r requirements.txt
KAFKA_BOOTSTRAP_SERVERS=localhost:9092 uvicorn main:app --reload --port 8000

# Terminal 3 — Frontend
cd frontend
npm install
npm run dev
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/posts/recent` | Recent processed posts |
| GET | `/api/trending` | Current trending topics |
| GET | `/api/sentiment` | Sentiment distribution |
| GET | `/api/sentiment/history` | Sentiment over time (Iceberg) |
| GET | `/api/stats` | System stats |
| POST | `/api/chat` | Chat with AI agent |
| WS | `/ws/feed` | Live post stream |

---

## AI Agent Tools

The LangChain agent has two tools it can call autonomously:

1. **search_posts** — Semantic search over posts using FAISS vector store. Finds posts related to any topic or keyword.
2. **query_trends** — Queries trending topics and sentiment data from both in-memory state and the Iceberg lakehouse.

Example conversations:
- "What's trending right now?" → agent calls `query_trends`
- "Find negative posts about Netflix" → agent calls `search_posts`
- "How has sentiment changed today?" → agent calls `query_trends` with time context

---

## Architecture

```
Post Simulator → Kafka (+ ZooKeeper) → Kafka Consumer
                                            ├── Sentiment Analysis (TextBlob)
                                            ├── Embedding Generation (Sentence-Transformers)
                                            ├── Iceberg Lakehouse (PyIceberg + Parquet)
                                            └── FAISS Vector Store
                                                    ↓
                                        FastAPI (REST + WebSocket)
                                        + LangChain AI Agent (Gemini)
                                                    ↓
                                        React Dashboard + AI Chat Panel
```

---

## Why These Technologies?

| Technology | Why Not the Simpler Alternative? |
|-----------|----------------------------------|
| **Kafka** (not REST API) | Posts arrive continuously — can't batch-process real-time trends. Kafka handles backpressure, ordering, and replay. |
| **ZooKeeper** | Manages Kafka broker coordination — leader election, topic metadata, consumer group state. |
| **Iceberg** (not PostgreSQL) | Time-travel queries ("sentiment 2 hours ago vs now"), schema evolution as new fields are added, partition pruning for fast scans over millions of posts. |
| **FAISS** (not full ChromaDB) | Lightweight in-memory vector search — no extra service needed. Good enough for semantic search over recent posts. |
| **LangChain agent** (not plain RAG) | Agent decides *which tool* to call based on the question — search vs trends vs both. ReAct pattern, not just "stuff context into prompt." |

---

## License

MIT
