import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Sparkles, Loader2 } from 'lucide-react'

const QUICK_PROMPTS = [
  "What's trending right now?",
  "Show me the sentiment summary",
  "Search posts about Netflix",
  "Any negative posts about Tesla?",
  "What topics are people talking about?",
]

export default function ChatPanel({ apiUrl, posts }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hey! I'm FeedPulse AI. I can search through live social media posts, analyze sentiment trends, and find what's buzzing. Try asking me something!",
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const chatEndRef = useRef(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (text) => {
    const userMsg = text || input.trim()
    if (!userMsg || loading) return

    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }])
    setLoading(true)

    try {
      const res = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg }),
      })
      const data = await res.json()
      setMessages((prev) => [...prev, { role: 'assistant', content: data.response }])
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, I had trouble connecting to the backend. Is the server running?' },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-surface-900 border border-surface-800 rounded-xl overflow-hidden flex flex-col" style={{ height: 'calc(100vh - 220px)' }}>
        {/* Chat header */}
        <div className="px-5 py-3.5 border-b border-surface-800 flex items-center gap-2">
          <Sparkles size={16} className="text-accent-light" />
          <span className="text-sm font-medium">FeedPulse AI Assistant</span>
          <span className="text-xs text-surface-700 ml-auto">Powered by Gemini + LangChain</span>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
              {msg.role === 'assistant' && (
                <div className="w-7 h-7 rounded-lg bg-accent/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Bot size={14} className="text-accent-light" />
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
                  msg.role === 'user'
                    ? 'bg-accent text-white'
                    : 'bg-surface-800 text-surface-200'
                }`}
              >
                {msg.content}
              </div>
              {msg.role === 'user' && (
                <div className="w-7 h-7 rounded-lg bg-surface-800 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <User size={14} className="text-surface-300" />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-3">
              <div className="w-7 h-7 rounded-lg bg-accent/20 flex items-center justify-center flex-shrink-0">
                <Bot size={14} className="text-accent-light" />
              </div>
              <div className="bg-surface-800 rounded-xl px-4 py-3 flex items-center gap-2">
                <Loader2 size={14} className="animate-spin text-accent-light" />
                <span className="text-sm text-surface-300">Analyzing posts...</span>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Quick prompts */}
        <div className="px-5 py-2 border-t border-surface-800/50 flex gap-2 overflow-x-auto">
          {QUICK_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              onClick={() => sendMessage(prompt)}
              className="px-3 py-1.5 rounded-lg text-xs text-surface-300 bg-surface-800 border border-surface-800 hover:border-accent/40 hover:text-white transition-colors whitespace-nowrap flex-shrink-0"
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Input */}
        <div className="px-4 py-3 border-t border-surface-800">
          <div className="flex items-center gap-2 bg-surface-800 rounded-xl px-4 py-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about trends, sentiment, or search posts..."
              className="flex-1 bg-transparent text-sm text-white placeholder-surface-700 outline-none"
              disabled={loading}
            />
            <button
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
              className="p-1.5 rounded-lg bg-accent hover:bg-accent-dark disabled:opacity-30 transition-colors"
            >
              <Send size={14} className="text-white" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
