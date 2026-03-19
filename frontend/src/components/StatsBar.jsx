import { Database, Cpu, Radio, Hash } from 'lucide-react'

export default function StatsBar({ stats, sentiment }) {
  const items = [
    {
      icon: <Radio size={14} />,
      label: 'Posts analyzed',
      value: sentiment?.total || 0,
      color: 'text-accent-light',
    },
    {
      icon: <Cpu size={14} />,
      label: 'Vectors stored',
      value: stats?.vectors_stored || 0,
      color: 'text-emerald-400',
    },
    {
      icon: <Database size={14} />,
      label: 'Iceberg snapshots',
      value: stats?.iceberg_snapshots || 0,
      color: 'text-sky-400',
    },
    {
      icon: <Hash size={14} />,
      label: 'Trending words',
      value: stats?.trending_words_tracked || 0,
      color: 'text-amber-400',
    },
  ]

  return (
    <div className="border-b border-surface-800 px-6 py-3 flex items-center gap-8 overflow-x-auto">
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-2 text-sm whitespace-nowrap">
          <span className={item.color}>{item.icon}</span>
          <span className="text-surface-300">{item.label}:</span>
          <span className="font-mono font-medium text-white">{item.value.toLocaleString()}</span>
        </div>
      ))}
    </div>
  )
}
