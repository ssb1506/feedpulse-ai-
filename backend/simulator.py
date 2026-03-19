"""
Post Simulator — Generates realistic social media posts and pushes them to Kafka.
Runs as a background thread inside the backend.
"""

import json
import random
import time
import threading
from datetime import datetime, timezone
from kafka import KafkaProducer

# ── Realistic post templates ──────────────────────────────────────────────────

TOPICS = {
    "tech": [
        "Just tried {product} and it's {opinion}. {hashtag}",
        "Anyone else having issues with {product}? {opinion} {hashtag}",
        "{product} just dropped a new update. {opinion}!",
        "Hot take: {product} is {opinion} compared to last year {hashtag}",
        "Finally switched to {product}. {opinion} so far {hashtag}",
    ],
    "sports": [
        "What a {opinion} game by {team} tonight! {hashtag}",
        "{team} really {opinion} this season. Thoughts? {hashtag}",
        "Can't believe {team} pulled that off. {opinion}! {hashtag}",
        "Watching {team} and it's been {opinion} all night {hashtag}",
    ],
    "food": [
        "Made {food} for dinner tonight. Turned out {opinion}! {hashtag}",
        "This {food} from the new place downtown is {opinion} {hashtag}",
        "Tried making {food} from a TikTok recipe. {opinion} results {hashtag}",
        "Nothing beats homemade {food}. {opinion} every time {hashtag}",
    ],
    "movies": [
        "Just watched {movie}. Honestly? {opinion}. {hashtag}",
        "{movie} is {opinion}. Don't @ me. {hashtag}",
        "Rewatching {movie} and it's still {opinion} after all these years {hashtag}",
        "The new {movie} trailer looks {opinion}! Can't wait {hashtag}",
    ],
    "general": [
        "Today was {opinion}. That's it. That's the post. {hashtag}",
        "Reminder: {opinion} things happen when you least expect them {hashtag}",
        "Monday mood: {opinion} {hashtag}",
        "Why is everything so {opinion} lately? {hashtag}",
    ],
}

PRODUCTS = ["ChatGPT", "iPhone 17", "Tesla", "Threads app", "Netflix", "Spotify", "Claude AI", "Vision Pro", "Windows 12", "Galaxy S26"]
TEAMS = ["Lakers", "Warriors", "Chiefs", "Yankees", "Man City", "Arsenal", "Celtics", "Dodgers"]
FOODS = ["pasta carbonara", "sushi", "tacos", "ramen", "pizza", "pad thai", "avocado toast", "bibimbap"]
MOVIES = ["Dune 3", "Oppenheimer", "Spider-Verse 3", "The Bear S4", "Severance S3", "Gladiator II"]

POSITIVE_OPINIONS = ["amazing", "incredible", "absolutely fantastic", "surprisingly great", "a total game-changer", "worth every penny", "so underrated", "pure fire"]
NEGATIVE_OPINIONS = ["terrible", "a complete disaster", "so disappointing", "honestly awful", "way overrated", "not worth the hype", "a total letdown", "getting worse"]
NEUTRAL_OPINIONS = ["okay I guess", "not bad not great", "pretty mid", "about what I expected", "interesting but nothing special", "decent enough"]

HASHTAGS = ["#trending", "#viral", "#rant", "#review", "#thoughts", "#unpopularopinion", "#honest", "#justmyopinion", "#mood", "#hot take"]

USERNAMES = [
    "alex_codes", "maya_creates", "dev_sarah", "techbro_mike", "nina_writes",
    "jake_reviews", "aria_thinks", "sam_rants", "jordan_vibes", "casey_posts",
    "morgan_says", "riley_reacts", "pat_shares", "quinn_updates", "drew_notes",
]


def generate_post() -> dict:
    """Generate a single fake social media post."""
    topic = random.choice(list(TOPICS.keys()))
    template = random.choice(TOPICS[topic])

    # Decide sentiment bias (60% mixed, 25% positive, 15% negative)
    roll = random.random()
    if roll < 0.25:
        opinion = random.choice(POSITIVE_OPINIONS)
        sentiment_hint = "positive"
    elif roll < 0.40:
        opinion = random.choice(NEGATIVE_OPINIONS)
        sentiment_hint = "negative"
    else:
        opinion = random.choice(POSITIVE_OPINIONS + NEGATIVE_OPINIONS + NEUTRAL_OPINIONS)
        sentiment_hint = "mixed"

    post_text = template.format(
        product=random.choice(PRODUCTS),
        team=random.choice(TEAMS),
        food=random.choice(FOODS),
        movie=random.choice(MOVIES),
        opinion=opinion,
        hashtag=random.choice(HASHTAGS),
    )

    return {
        "id": f"post_{int(time.time() * 1000)}_{random.randint(100, 999)}",
        "username": random.choice(USERNAMES),
        "text": post_text,
        "topic": topic,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "likes": random.randint(0, 500),
        "reposts": random.randint(0, 100),
    }


from kafka_config import get_producer_config


class PostSimulator:
    """Continuously generates posts and sends them to Kafka."""

    def __init__(self, topic: str = "social-posts"):
        self.topic = topic
        self.producer = None
        self._running = False

    def _connect_producer(self, retries: int = 10, delay: int = 5):
        """Connect to Kafka with retries (Kafka takes a while to start)."""
        for attempt in range(retries):
            try:
                config = get_producer_config()
                self.producer = KafkaProducer(
                    **config,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                )
                print(f"[Simulator] Connected to Kafka")
                return
            except Exception as e:
                print(f"[Simulator] Kafka not ready (attempt {attempt + 1}/{retries}): {e}")
                time.sleep(delay)
        raise ConnectionError("Could not connect to Kafka after retries")

    def start(self):
        """Start producing posts in a background thread."""
        self._running = True
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()
        print("[Simulator] Post generation started")

    def stop(self):
        self._running = False

    def _run(self):
        self._connect_producer()
        while self._running:
            post = generate_post()
            self.producer.send(self.topic, value=post)
            self.producer.flush()
            # Random delay between 0.5 and 2 seconds
            time.sleep(random.uniform(0.5, 2.0))
