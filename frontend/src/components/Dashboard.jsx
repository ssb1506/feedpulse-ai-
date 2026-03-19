import { useState, useEffect } from 'react'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from 'recharts'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

const COLORS = {
  positive: '#22c55e',
  negative: '#ef4444',
  neutral: '#64748b',
}

export default function Dashboard({ sentiment, posts, apiUrl }) {
  const [sentimentHistory, setSentimentHistory] = useState([])

  // Build live sentiment-over-time from incoming posts
  useEffect(() => {
    if (posts.length === 0) return

    // Group last 100 posts into 10 buckets for a smooth chart
    const bucketSize = Math.max(1, Math.floor(posts.length / 10))
    const buckets = []

    for (let i = 0; i < Math.min(posts.length, 100); i += bucketSize) {
      const slice = posts.slice(i, i + bucketSize)
      const avgScore = slice.reduce((sum, p) => sum + (p.sentiment_score || 0), 0) / slice.length
      const time = slice[0]?.timestamp
        ? new Date(slice[0].timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        : ''

      buckets.push({
        time,
        sentiment: parseFloat(avgScore.toFixed(3)),
        posts: slice.length,
      })
    }

    setSentimentHistory(buckets.reverse())
  }, [posts])

  const total = sentiment.total || 1
  const pieData = [
    { name: 'Positive', value: sentiment.positive, color: COLORS.positive },
    { name: 'Negative', value: sentiment.negative, color: COLORS.negative },
    { name: 'Neutral', value: sentiment.neutral, color: COLORS.neutral },
  ]

  const dominantSentiment = sentiment.positive >= sentiment.negative ? 'positive' : 'negative'

  return (
    <div className="space-y-6">
      {/* Sentiment over time chart */}
      <div className="bg-surface-900 border border-surface-800 rounded-xl p-5">
        <h3 className="text-sm font-medium text-surface-300 mb-4">Sentiment over time</h3>
        <div className="h-52">
          {sentimentHistory.length > 1 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={sentimentHistory}>
                <defs>
                  <linearGradient id="sentGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="time"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#64748b', fontSize: 11 }}
                />
                <YAxis
                  domain={[-1, 1]}
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#64748b', fontSize: 11 }}
                  width={35}
                />
                <Tooltip
                  contentStyle={{
                    background: '#1c2128',
                    border: '1px solid #30363d',
                    borderRadius: '8px',
                    fontSize: '12px',
                    color: '#e6edf3',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="sentiment"
                  stroke="#6366f1"
                  strokeWidth={2}
                  fill="url(#sentGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-surface-700 text-sm">
              Waiting for posts to chart...
            </div>
          )}
        </div>
      </div>

      {/* Sentiment breakdown */}
      <div className="grid grid-cols-2 gap-4">
        {/* Pie chart */}
        <div className="bg-surface-900 border border-surface-800 rounded-xl p-5">
          <h3 className="text-sm font-medium text-surface-300 mb-3">Sentiment split</h3>
          <div className="h-40">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={65}
                  dataKey="value"
                  stroke="none"
                >
                  {pieData.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-4 mt-2">
            {pieData.map((item) => (
              <div key={item.name} className="flex items-center gap-1.5 text-xs">
                <span className="w-2 h-2 rounded-full" style={{ background: item.color }} />
                <span className="text-surface-300">{item.name}</span>
                <span className="font-mono text-white">{item.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Sentiment cards */}
        <div className="space-y-3">
          <div className="bg-surface-900 border border-surface-800 rounded-xl p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-surface-300">Positive</p>
              <p className="text-2xl font-semibold text-positive font-mono">
                {total > 0 ? Math.round((sentiment.positive / total) * 100) : 0}%
              </p>
            </div>
            <TrendingUp size={24} className="text-positive/40" />
          </div>
          <div className="bg-surface-900 border border-surface-800 rounded-xl p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-surface-300">Negative</p>
              <p className="text-2xl font-semibold text-negative font-mono">
                {total > 0 ? Math.round((sentiment.negative / total) * 100) : 0}%
              </p>
            </div>
            <TrendingDown size={24} className="text-negative/40" />
          </div>
          <div className="bg-surface-900 border border-surface-800 rounded-xl p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-surface-300">Neutral</p>
              <p className="text-2xl font-semibold text-neutral font-mono">
                {total > 0 ? Math.round((sentiment.neutral / total) * 100) : 0}%
              </p>
            </div>
            <Minus size={24} className="text-neutral/40" />
          </div>
        </div>
      </div>
    </div>
  )
}
