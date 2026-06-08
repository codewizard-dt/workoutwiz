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
import type { WeeklyComparisonPoint } from '../types'

interface Props {
  data: WeeklyComparisonPoint[]
}

export function WeeklyComparisonChart({ data }: Props) {
  if (data.length < 1) return null

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
        <Bar dataKey="adherence_pct" name="Adherence %" fill="var(--chart-1)" radius={[3, 3, 0, 0]} />
        <Bar dataKey="workouts_completed" name="Workouts" fill="var(--chart-3)" radius={[3, 3, 0, 0]} />
        <Bar dataKey="messages_sent" name="Messages" fill="var(--chart-5)" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
