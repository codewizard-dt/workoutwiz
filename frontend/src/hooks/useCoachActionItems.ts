import { useMemo } from 'react'
import type { ActionItem, AdherenceWeek, ChurnRisk } from '../types'

export function useCoachActionItems(
  memberId: string,
  memberName: string,
  adherenceWeeks: AdherenceWeek[],
  churnRisk: ChurnRisk,
): ActionItem[] {
  return useMemo(() => {
    const items: ActionItem[] = []

    if (churnRisk.level === 'high') {
      items.push({
        priority: 'high',
        member_id: memberId,
        member_name: memberName,
        reason: `High churn risk: ${churnRisk.reasons.join('; ')}`,
        context: { churn_level: churnRisk.level, churn_reasons: churnRisk.reasons },
      })
    }

    if (adherenceWeeks.length > 0) {
      const latest = adherenceWeeks[adherenceWeeks.length - 1]
      if (latest.pct < 50) {
        items.push({
          priority: 'high',
          member_id: memberId,
          member_name: memberName,
          reason: `Low adherence this week: ${latest.pct}% (week of ${latest.week_of})`,
          context: { week_of: latest.week_of, adherence_pct: latest.pct },
        })
      } else if (latest.pct < 70) {
        items.push({
          priority: 'medium',
          member_id: memberId,
          member_name: memberName,
          reason: `Below-target adherence this week: ${latest.pct}% (week of ${latest.week_of})`,
          context: { week_of: latest.week_of, adherence_pct: latest.pct },
        })
      }
    }

    const order: Record<string, number> = { high: 0, medium: 1, low: 2 }
    return items.sort((a, b) => (order[a.priority] ?? 3) - (order[b.priority] ?? 3))
  }, [memberId, memberName, adherenceWeeks, churnRisk])
}
