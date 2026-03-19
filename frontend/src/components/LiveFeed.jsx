import { ThumbsUp, Repeat2 } from 'lucide-react'

const SENTIMENT_STYLES = {
  positive: 'border-l-positive/60',
  negative: 'border-l-negative/60',
  neutral: 'border-l-surface-700',
}

const SENTIMENT_BADGE = {
  positive: 'bg-positive/10 text-positive',
  negative: 'bg-negative/10 text-negative',
  neutral: 'bg-surface-800 text-surface-300',
}

const TOPIC_EMOJI = {
  tech: '💻',
  sports: '⚽',
  food: '🍕',
  movies: '🎬',
  general: '💬',
}

export default function LiveFeed({ posts }) {
  return (
    <div className="bg-surface-900 border border-surface-800 rounded-xl">
      <div className="px-5 py-3.5 border-b border-surface-800 flex items-center justify-between">
        <h3 className="text-sm font-medium text-surface-300">Live feed</h3>
        <span className="text-xs text-surface-700 font-mono">{posts.length} posts</span>
      </div>

      <div className="max-h-[600px] overflow-y-auto">
        {posts.length === 0 ? (
          <div className="p-8 text-center text-surface-700 text-sm">
            Waiting for posts to arrive...
          </div>
        ) : (
          posts.slice(0, 50).map((post, i) => (
            <div
              key={post.id || i}
              className={`slide-in border-l-2 ${SENTIMENT_STYLES[post.sentiment_label] || SENTIMENT_STYLES.neutral} px-4 py-3 border-b border-surface-800/50 hover:bg-surface-800/30 transition-colors`}
            >
              {/* Header: username + topic + time */}
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-white">@{post.username}</span>
                  <span className="text-xs">{TOPIC_EMOJI[post.topic] || '💬'}</span>
                </div>
                <span className="text-[10px] text-surface-700 font-mono">
                  {post.timestamp
                    ? new Date(post.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
                    : ''}
                </span>
              </div>

              {/* Post text */}
              <p className="text-sm text-surface-200 leading-relaxed mb-2">{post.text}</p>

              {/* Footer: sentiment badge + likes/reposts */}
              <div className="flex items-center justify-between">
                <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${SENTIMENT_BADGE[post.sentiment_label] || SENTIMENT_BADGE.neutral}`}>
                  {post.sentiment_label} ({post.sentiment_score > 0 ? '+' : ''}{post.sentiment_score})
                </span>
                <div className="flex items-center gap-3 text-surface-700">
                  <span className="flex items-center gap-1 text-xs">
                    <ThumbsUp size={11} />
                    {post.likes}
                  </span>
                  <span className="flex items-center gap-1 text-xs">
                    <Repeat2 size={11} />
                    {post.reposts}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
