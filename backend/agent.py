"""
AI Agent — LangChain agent with two tools:
1. search_posts: Semantic search over recent posts via FAISS
2. query_trends: Query historical sentiment/trends from Iceberg lakehouse
"""

import os
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate


AGENT_PROMPT = PromptTemplate.from_template("""You are FeedPulse AI — a social media analytics assistant.
You help users understand what's happening on social media by analyzing posts, sentiment, and trends.

You have access to the following tools:

{tools}

Tool names: {tool_names}

When answering questions:
- Use search_posts to find specific posts related to a topic or keyword
- Use query_trends to get historical sentiment data and trending topics
- Always cite specific posts or data when making claims
- Be conversational and insightful, not just listing data

Question: {input}

{agent_scratchpad}""")


class FeedPulseAgent:
    """AI agent that can search posts and query trends."""

    def __init__(self, vector_store, iceberg_store, consumer):
        self.vector_store = vector_store
        self.iceberg_store = iceberg_store
        self.consumer = consumer
        self.agent = None
        self._setup_agent()

    def _setup_agent(self):
        """Initialize the LangChain agent with tools."""
        api_key = os.getenv("GEMINI_API_KEY", "")

        if not api_key or api_key == "your-api-key-here":
            print("[Agent] WARNING: No GEMINI_API_KEY set. Agent will use fallback mode.")
            self.agent = None
            return

        try:
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=api_key,
                temperature=0.3,
            )

            tools = [
                Tool(
                    name="search_posts",
                    description="Search for social media posts by topic, keyword, or sentiment. Input should be a natural language search query like 'negative posts about Tesla' or 'what are people saying about Netflix'.",
                    func=self._search_posts,
                ),
                Tool(
                    name="query_trends",
                    description="Get trending topics, sentiment summaries, and historical data. Input can be 'trending', 'sentiment summary', or 'sentiment over time'.",
                    func=self._query_trends,
                ),
            ]

            agent = create_react_agent(llm, tools, AGENT_PROMPT)
            self.agent = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=3,
            )
            print("[Agent] Initialized with Gemini LLM")

        except Exception as e:
            print(f"[Agent] Error initializing: {e}")
            self.agent = None

    def _search_posts(self, query: str) -> str:
        """Tool: Search posts via FAISS vector store."""
        results = self.vector_store.search(query, top_k=5)
        if not results:
            return "No posts found matching that query yet. The system is still collecting data."

        output = []
        for post in results:
            output.append(
                f"- @{post['username']}: \"{post['text']}\" "
                f"[sentiment: {post.get('sentiment_label', 'unknown')}, "
                f"score: {post.get('sentiment_score', 0)}, "
                f"relevance: {post.get('relevance_score', 0)}]"
            )
        return "\n".join(output)

    def _query_trends(self, query: str) -> str:
        """Tool: Query trending topics and sentiment from Iceberg + in-memory."""
        query_lower = query.lower()

        if "trending" in query_lower:
            trends = self.consumer.get_trending(top_n=10)
            if not trends:
                return "No trending data yet. Posts are still being collected."
            return "Top trending words:\n" + "\n".join(
                f"- '{t['word']}': mentioned {t['count']} times" for t in trends
            )

        elif "sentiment" in query_lower and "time" in query_lower:
            data = self.iceberg_store.get_sentiment_over_time(hours=6)
            if not data:
                return "Not enough historical data yet for time-based analysis."
            output = "Sentiment over time:\n"
            for row in data:
                output += (
                    f"- {row['hour']}: avg={row['avg_sentiment']:.2f}, "
                    f"posts={row['post_count']}, "
                    f"+{row['positive']}/-{row['negative']}/{row['neutral']} neutral\n"
                )
            return output

        else:
            summary = self.consumer.get_sentiment_summary()
            trends = self.consumer.get_trending(top_n=5)
            return (
                f"Current sentiment: {summary['positive']} positive, "
                f"{summary['negative']} negative, {summary['neutral']} neutral "
                f"(out of {summary['total']} recent posts).\n"
                f"Top trending: {', '.join(t['word'] for t in trends) if trends else 'collecting data...'}"
            )

    async def chat(self, message: str) -> str:
        """Process a user message and return the agent's response."""
        if not self.agent:
            return self._fallback_response(message)

        try:
            result = self.agent.invoke({"input": message})
            return result.get("output", "I couldn't process that. Try asking about trends or specific topics.")
        except Exception as e:
            print(f"[Agent] Error: {e}")
            return self._fallback_response(message)

    def _fallback_response(self, message: str) -> str:
        """Fallback when LLM is not available — uses tools directly."""
        msg_lower = message.lower()

        if "trending" in msg_lower or "trend" in msg_lower:
            return self._query_trends("trending")
        elif "sentiment" in msg_lower:
            return self._query_trends("sentiment summary")
        elif "search" in msg_lower or "find" in msg_lower or "about" in msg_lower:
            return self._search_posts(message)
        else:
            summary = self.consumer.get_sentiment_summary()
            trends = self.consumer.get_trending(top_n=5)
            top_words = ", ".join(t["word"] for t in trends) if trends else "still collecting"
            return (
                f"Here's a quick overview:\n\n"
                f"Posts analyzed: {summary['total']}\n"
                f"Sentiment: {summary['positive']} positive, {summary['negative']} negative, "
                f"{summary['neutral']} neutral\n"
                f"Trending: {top_words}\n\n"
                f"Try asking: 'What's trending?', 'Search posts about Tesla', "
                f"or 'What's the sentiment summary?'"
            )
