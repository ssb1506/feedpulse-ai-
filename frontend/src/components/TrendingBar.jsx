import { TrendingUp } from 'lucide-react'

export default function TrendingBar({ trending }) {
  if (!trending || trending.length === 0) return null

  return (
    <div className="border-b border-surface-800 px-6 py-2.5 flex items-center gap-3 overflow-x-auto">
      <div className="flex items-center gap-1.5 text-sm text-accent-light whitespace-nowrap">
        <TrendingUp size={14} />
        <span className="font-medium">Trending</span>
      </div>
      <div className="flex items-center gap-2">
        {trending.map((item, i) => (
          <span
            key={item.word}
            className="px-2.5 py-1 rounded-full text-xs font-medium whitespace-nowrap bg-surface-900 text-surface-300 border border-surface-800 hover:border-accent/40 hover:text-white transition-colors cursor-default"
          >
            {item.word}
            <span className="ml-1.5 text-surface-700 font-mono">{item.count}</span>
          </span>
        ))}
      </div>
    </div>
  )
}
