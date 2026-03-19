import { useState, useEffect } from 'react'
import useWebSocket from './hooks/useWebSocket'
import Dashboard from './components/Dashboard'
import ChatPanel from './components/ChatPanel'
import LiveFeed from './components/LiveFeed'
import TrendingBar from './components/TrendingBar'
import StatsBar from './components/StatsBar'
import { Activity, MessageSquare, BarChart3 } from 'lucide-react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App() {
  const { posts, connected } = useWebSocket()
  const [view, setView] = useState('dashboard') // 'dashboard' or 'chat'
  const [stats, setStats] = useState(null)
  const [trending, setTrending] = useState([])
  const [sentiment, setSentiment] = useState({ positive: 0, negative: 0, neutral: 0, total: 0 })

  // Poll stats, trending, sentiment every 5 seconds
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, trendRes, sentRes] = await Promise.all([
          fetch(`${API}/api/stats`),
          fetch(`${API}/api/trending?top_n=8`),
          fetch(`${API}/api/sentiment`),
        ])
        setStats(await statsRes.json())
        const trendData = await trendRes.json()
        setTrending(trendData.trending || [])
        setSentiment(await sentRes.json())
      } catch (e) {
        console.error('Fetch error:', e)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-surface-950 text-white">
      {/* Header */}
      <header className="border-b border-surface-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-accent flex items-center justify-center">
            <Activity size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-lg font-semibold tracking-tight">FeedPulse AI</h1>
            <p className="text-xs text-surface-300">Real-time social media analytics</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Live indicator */}
          <div className="flex items-center gap-2 text-sm">
            <span className={`w-2 h-2 rounded-full ${connected ? 'bg-positive pulse-dot' : 'bg-negative'}`} />
            <span className="text-surface-300">{connected ? 'Live' : 'Connecting...'}</span>
          </div>

          {/* View toggle */}
          <div className="flex bg-surface-900 rounded-lg p-1 gap-1">
            <button
              onClick={() => setView('dashboard')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors ${
                view === 'dashboard' ? 'bg-accent text-white' : 'text-surface-300 hover:text-white'
              }`}
            >
              <BarChart3 size={14} />
              Dashboard
            </button>
            <button
              onClick={() => setView('chat')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors ${
                view === 'chat' ? 'bg-accent text-white' : 'text-surface-300 hover:text-white'
              }`}
            >
              <MessageSquare size={14} />
              AI Assistant
            </button>
          </div>
        </div>
      </header>

      {/* Stats bar */}
      <StatsBar stats={stats} sentiment={sentiment} />

      {/* Trending bar */}
      <TrendingBar trending={trending} />

      {/* Main content */}
      <main className="px-6 py-4">
        {view === 'dashboard' ? (
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
            <div className="lg:col-span-3">
              <Dashboard sentiment={sentiment} posts={posts} apiUrl={API} />
            </div>
            <div className="lg:col-span-2">
              <LiveFeed posts={posts} />
            </div>
          </div>
        ) : (
          <ChatPanel apiUrl={API} posts={posts} />
        )}
      </main>
    </div>
  )
}
