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

  const maxWorkouts = Math.max(...data.map((d) => d.workouts_completed), 1)
  const maxMessages = Math.max(...data.map((d) => d.messages_sent), 1)

  const formatted = data.map((d) => ({
    ...d,
    week: d.week_of.slice(5),
    workouts_norm: (d.workouts_completed / maxWorkouts) * 100,
    messages_norm: (d.messages_sent / maxMessages) * 100,
  }))

  const tooltipFormatter = (
    value: number,
    name: string,
    props: { payload: typeof formatted[number] },
  ) => {
    if (name === 'Workouts') return [props.payload.workouts_completed, name]
    if (name === 'Messages') return [props.payload.messages_sent, name]
    return [Math.round(value), name]
  }

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
          domain={[0, 100]}
          allowDecimals={false}
          tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          formatter={tooltipFormatter}
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
        <Bar dataKey="workouts_norm" name="Workouts" fill="var(--chart-3)" radius={[3, 3, 0, 0]} />
        <Bar dataKey="messages_norm" name="Messages" fill="var(--chart-5)" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
