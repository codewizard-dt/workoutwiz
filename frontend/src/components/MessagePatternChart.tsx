import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import type { MessagePatternPoint } from '../types'

interface Props {
  data: MessagePatternPoint[]
}

export function MessagePatternChart({ data }: Props) {
  if (data.length === 0) return null

  const formatted = data.map((d) => ({
    ...d,
    week: d.week_of.slice(5), // MM-DD
  }))

  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={formatted} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis
          dataKey="week"
          tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{
            background: 'var(--card)',
            border: '1px solid var(--border)',
            borderRadius: '0.5rem',
            fontSize: '0.8rem',
            color: 'var(--foreground)',
          }}
        />
        <Legend
          wrapperStyle={{ fontSize: '0.75rem', color: 'var(--muted-foreground)' }}
        />
        <Bar dataKey="member_count" name="Member" fill="var(--chart-1)" radius={[3, 3, 0, 0]} />
        <Bar dataKey="coach_count" name="Coach" fill="var(--chart-2)" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
