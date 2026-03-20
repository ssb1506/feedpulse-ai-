"""
Kafka Consumer — Reads posts from Kafka, processes them (sentiment + embeddings),
stores in Iceberg lakehouse and FAISS vector store.
"""

import json
import time
import threading
from datetime import datetime, timezone
from typing import Callable

from kafka import KafkaConsumer
from textblob import TextBlob

from iceberg_store import IcebergStore
from vector_store import VectorStore


def analyze_sentiment(text: str) -> dict:
    """Simple sentiment analysis using TextBlob."""
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity  # -1.0 to 1.0

    if polarity > 0.1:
        label = "positive"
    elif polarity < -0.1:
        label = "negative"
    else:
        label = "neutral"

    return {"label": label, "score": round(polarity, 3)}


def detect_trending_words(text: str) -> list[str]:
    """Extract notable words from a post (simple keyword extraction)."""
    blob = TextBlob(text)
    # Get nouns and adjectives as potential trending words
    words = []
    for word, tag in blob.tags:
        if tag in ("NN", "NNP", "JJ") and len(word) > 3 and not word.startswith("#"):
            words.append(word.lower())
    return words


from kafka_config import get_consumer_config


class PostConsumer:
    """Consumes posts from Kafka, enriches them, stores everywhere."""

    def __init__(
        self,
        topic: str = "social-posts",
        on_post: Callable = None,
    ):
        self.topic = topic
        self.on_post = on_post  # callback for WebSocket broadcast
        self.iceberg = IcebergStore()
        self.vectors = VectorStore()
        self._running = False

        # In-memory trending tracker
        self.trending_counts: dict[str, int] = {}
        self.recent_posts: list[dict] = []  # last 100 posts for quick access

    def _connect_consumer(self, retries: int = 15, delay: int = 5):
        """Connect to Kafka with retries."""
        for attempt in range(retries):
            try:
                config = get_consumer_config()
                consumer = KafkaConsumer(
                    self.topic,
                    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                    auto_offset_reset="latest",
                    enable_auto_commit=True,
                    group_id="feedpulse-consumer",
                    consumer_timeout_ms=1000,
                    **config,
                )
                print(f"[Consumer] Connected to Kafka topic '{self.topic}'")
                return consumer
            except Exception as e:
                print(f"[Consumer] Kafka not ready (attempt {attempt + 1}/{retries}): {e}")
                time.sleep(delay)
        raise ConnectionError("Could not connect to Kafka consumer")

    def start(self):
        """Start consuming in a background thread."""
        self._running = True
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()
        print("[Consumer] Started processing posts")

    def stop(self):
        self._running = False

    def _run(self):
        consumer = self._connect_consumer()

        while self._running:
            try:
                # Poll for messages
                for message in consumer:
                    if not self._running:
                        break
                    self._process_post(message.value)
            except Exception as e:
                print(f"[Consumer] Error: {e}")
                time.sleep(2)

    def _process_post(self, post: dict):
        """Process a single post: sentiment + embedding + store."""
        try:
            # 1. Sentiment analysis
            sentiment = analyze_sentiment(post["text"])
            post["sentiment_label"] = sentiment["label"]
            post["sentiment_score"] = sentiment["score"]

            # 2. Trending word extraction
            keywords = detect_trending_words(post["text"])
            post["keywords"] = keywords
            for word in keywords:
                self.trending_counts[word] = self.trending_counts.get(word, 0) + 1

            # 3. Store in FAISS vector store
            self.vectors.add_post(post)

            # 4. Store in Iceberg lakehouse
            self.iceberg.append_post(post)

            # 5. Keep in recent memory
            self.recent_posts.append(post)
            if len(self.recent_posts) > 200:
                self.recent_posts = self.recent_posts[-200:]

            # 6. Broadcast to WebSocket listeners
            if self.on_post:
                self.on_post(post)

            print(f"[Consumer] Processed: [{sentiment['label']}] {post['text'][:60]}...")

        except Exception as e:
            print(f"[Consumer] Error processing post: {e}")

    def get_trending(self, top_n: int = 10) -> list[dict]:
        """Get top trending words."""
        sorted_words = sorted(self.trending_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"word": w, "count": c} for w, c in sorted_words[:top_n]]

    def get_sentiment_summary(self) -> dict:
        """Get sentiment distribution of recent posts."""
        if not self.recent_posts:
            return {"positive": 0, "negative": 0, "neutral": 0, "total": 0}

        counts = {"positive": 0, "negative": 0, "neutral": 0}
        for post in self.recent_posts:
            label = post.get("sentiment_label", "neutral")
            counts[label] = counts.get(label, 0) + 1

        return {**counts, "total": len(self.recent_posts)}
