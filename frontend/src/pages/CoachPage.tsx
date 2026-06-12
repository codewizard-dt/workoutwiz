import { useEffect, useRef, useState, type KeyboardEvent, type ChangeEvent } from 'react'
import { PartyPopper, AlertTriangle, TrendingDown, TrendingUp, ImageIcon, X, Info } from 'lucide-react'
import { useCoachBrief } from '../hooks/useCoachBrief'
import { useCoachActionItems } from '../hooks/useCoachActionItems'
import { useCoachNudge } from '../hooks/useCoachNudge'
import { useCoachChat } from '../hooks/useCoachChat'
import { useCoachMembers } from '../hooks/useCoachMembers'
import { ChatBubble } from '@/components/ChatBubble'
import { TypingBubble } from '@/components/TypingBubble'
import { MessagePatternChart } from '@/components/MessagePatternChart'
import { WeeklyComparisonChart } from '@/components/WeeklyComparisonChart'
import { useCoachDrafts } from '../hooks/useCoachDrafts'
import { useCoachDraftActions } from '../hooks/useCoachDraftActions'

const QUICK_PROMPTS = [
  'Show me the brief',
  "How's adherence trending?",
  'Sleep this week',
  'What changed since last week?',
  'Churn risk summary',
  'Latest workout recap',
] as const

const CHURN_COLORS: Record<string, string> = {
  elevated: 'var(--destructive)',
  moderate: 'var(--accent)',
  low: 'var(--success)',
}

// ── Adherence bar chart (pure CSS) ──────────────────────────────────────────

function AdherenceChart({ weeks }: { weeks: { week_of: string; pct: number }[] }) {
  if (!weeks.length) return null

  const maxPct = 100
  const barColor = (pct: number) =>
    pct >= 90 ? 'var(--success)' : pct >= 60 ? 'var(--accent)' : 'var(--destructive)'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
      {weeks.map((w) => (
        <div key={w.week_of} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <span style={{ width: '5rem', fontSize: '0.75rem', color: 'var(--muted-foreground)', flexShrink: 0 }}>
            {w.week_of.slice(5)}
          </span>
          <div
            style={{
              flex: 1,
              height: '1.25rem',
              background: 'var(--muted)',
              borderRadius: '0.25rem',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                height: '100%',
                width: `${(w.pct / maxPct) * 100}%`,
                background: barColor(w.pct),
                borderRadius: '0.25rem',
                transition: 'width 0.4s ease',
              }}
            />
          </div>
          <span
            style={{
              width: '2.5rem',
              textAlign: 'right',
              fontSize: '0.8rem',
              fontWeight: 600,
              color: barColor(w.pct),
              flexShrink: 0,
            }}
          >
            {w.pct}%
          </span>
        </div>
      ))}
    </div>
  )
}

// ── Main page ────────────────────────────────────────────────────────────────

// ── Action Items card ────────────────────────────────────────────────────────

function ActionItemsCard({
  memberId,
  memberName,
  adherenceWeeks,
  churnRisk,
}: {
  memberId: string
  memberName: string
  adherenceWeeks: import('../types').AdherenceWeek[]
  churnRisk: import('../types').ChurnRisk
}) {
  const actionItems = useCoachActionItems(memberId, memberName, adherenceWeeks, churnRisk)
  const { draftNudge, isLoading: nudgeLoading } = useCoachNudge()
  const [nudgeDrafts, setNudgeDrafts] = useState<Record<number, string>>({})

  if (actionItems.length === 0) return null

  return (
    <div style={{ background: 'color-mix(in srgb, var(--ember-500) 4%, var(--card))', border: '1px solid var(--ember-300)', borderLeft: '3px solid var(--ember-500)', borderRadius: '0.75rem', padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
      <div style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--ember-600)' }}>
        Action Items
      </div>
      {actionItems.map((item, i) => (
        <div key={i} style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'flex-start', background: item.priority === 'high' ? 'color-mix(in srgb, var(--destructive) 8%, var(--card))' : 'var(--card)', border: item.priority === 'high' ? '1px solid color-mix(in srgb, var(--destructive) 25%, transparent)' : '1px solid var(--border)', borderRadius: '0.5rem', padding: 'var(--space-3)' }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', color: item.priority === 'high' ? 'var(--destructive)' : 'var(--muted-foreground)', marginBottom: '0.2rem' }}>
              {item.priority}
            </div>
            <div style={{ fontSize: '0.85rem', lineHeight: 1.4 }}>{item.reason}</div>
            {nudgeDrafts[i] && (
              <div style={{ marginTop: 'var(--space-2)', fontSize: '0.85rem', background: 'var(--accent)', borderRadius: '0.375rem', padding: 'var(--space-2)', color: 'var(--accent-foreground)', lineHeight: 1.5 }}>
                {nudgeDrafts[i]}
              </div>
            )}
          </div>
          <button
            type="button"
            className="ww-btn ww-btn--sm ww-btn--ghost"
            disabled={nudgeLoading}
            onClick={() => {
              void draftNudge(memberId, memberName, item).then(result => {
                if (result) setNudgeDrafts(prev => ({ ...prev, [i]: result.draft_message }))
              })
            }}
            style={{ flexShrink: 0, fontSize: '0.75rem' }}
          >
            Draft Nudge
          </button>
        </div>
      ))}
    </div>
  )
}

// ── Pending Drafts panel ──────────────────────────────────────────────────────

function PendingDraftsPanel({ memberId }: { memberId: string }) {
  const { data: drafts, isLoading } = useCoachDrafts(memberId)
  const { patchDraft, isLoading: actionLoading } = useCoachDraftActions()
  const [editBodies, setEditBodies] = useState<Record<string, string>>({})

  if (isLoading || !drafts || drafts.length === 0) return null

  return (
    <div style={{ background: 'color-mix(in srgb, var(--ember-500) 4%, var(--card))', border: '1px solid var(--ember-300)', borderLeft: '3px solid var(--ember-500)', borderRadius: '0.75rem', padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
      <div style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--ember-600)' }}>
        Pending Drafts
      </div>
      {drafts.map((draft) => {
        const currentBody = editBodies[draft.id] ?? draft.body
        const isEdited = currentBody !== draft.body
        const canSend = draft.status === 'approved' && !isEdited
        return (
          <div key={draft.id} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', background: 'var(--card)', border: '1px solid var(--border)', borderRadius: '0.5rem', padding: 'var(--space-3)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', color: draft.status === 'approved' ? 'var(--success)' : 'var(--muted-foreground)' }}>
                {draft.status} · {draft.content_type}
              </span>
              <span style={{ fontSize: '0.7rem', color: 'var(--muted-foreground)' }}>
                {new Date(draft.created_at).toLocaleTimeString()}
              </span>
            </div>
            <textarea
              className="ww-scroll"
              style={{ width: '100%', minHeight: '4rem', borderRadius: '0.375rem', border: '1px solid var(--border)', background: 'var(--background)', padding: '0.5rem 0.75rem', fontSize: '0.85rem', fontFamily: 'inherit', color: 'inherit', resize: 'vertical' }}
              value={currentBody}
              onChange={(e) => { setEditBodies((prev) => ({ ...prev, [draft.id]: e.target.value })) }}
            />
            {draft.grounded_on.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-1)' }}>
                {draft.grounded_on.map((fact, i) => (
                  <span key={i} className="ww-badge ww-badge--amber">{fact}</span>
                ))}
              </div>
            )}
            <div style={{ display: 'flex', gap: 'var(--space-2)', justifyContent: 'flex-end' }}>
              {isEdited && (
                <button
                  type="button"
                  className="ww-btn ww-btn--sm ww-btn--ghost"
                  disabled={actionLoading}
                  onClick={() => {
                    void patchDraft(draft.id, 'edit', currentBody).then(() => {
                      setEditBodies((prev) => {
                        const { [draft.id]: _discarded, ...rest } = prev
                        void _discarded
                        return rest
                      })
                    })
                  }}
                >
                  Save Edit
                </button>
              )}
              {draft.status === 'draft' && !isEdited && (
                <button
                  type="button"
                  className="ww-btn ww-btn--sm"
                  disabled={actionLoading}
                  onClick={() => { void patchDraft(draft.id, 'approve') }}
                >
                  Approve
                </button>
              )}
              <button
                type="button"
                className="ww-btn ww-btn--sm ww-btn--gradient"
                disabled={!canSend || actionLoading}
                title={!canSend ? 'Draft must be approved before sending' : undefined}
                onClick={() => { void patchDraft(draft.id, 'send') }}
              >
                Send
              </button>
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default function CoachPage() {
  const { data: members } = useCoachMembers()
  const [selectedMemberId, setSelectedMemberId] = useState<string | null>(null)
  const [loadedMembersKey, setLoadedMembersKey] = useState<string | null>(null)

  // Default to first member once the list loads — derive in render to avoid useEffect+setState lint error
  const firstMemberId = members && members.length > 0 ? members[0].member_id : null
  if (firstMemberId !== null && selectedMemberId === null && loadedMembersKey !== firstMemberId) {
    setLoadedMembersKey(firstMemberId)
    setSelectedMemberId(firstMemberId)
  }

  const { data: brief, isLoading: briefLoading, error: briefQueryError } = useCoachBrief(selectedMemberId)
  const briefError = briefQueryError?.message ?? null
  const { messages, sendMessage, isLoading: chatLoading, error: chatError } = useCoachChat(selectedMemberId)

  const [draft, setDraft] = useState('')
  const [pendingImage, setPendingImage] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, chatLoading])

  async function handleSend(text?: string) {
    const msg = (text ?? draft).trim()
    if ((!msg && !pendingImage) || chatLoading) return
    setDraft('')
    const img = pendingImage
    setPendingImage(null)
    await sendMessage(msg, img ?? undefined)
  }

  function handleImageChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => { setPendingImage(reader.result as string) }
    reader.readAsDataURL(file)
    // reset so the same file can be re-selected
    e.target.value = ''
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void handleSend()
    }
  }

  const churnLevel = brief?.churn_risk.level ?? 'unknown'
  const churnColor = CHURN_COLORS[churnLevel] ?? 'var(--muted-foreground)'
  const [bannerDismissed, setBannerDismissed] = useState(false)

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        flex: 1,
        padding: 'var(--space-5) var(--space-4)',
        gap: 'var(--space-5)',
        maxWidth: '1100px',
        width: '100%',
        margin: '0 auto',
      }}
    >
      {/* ── Demo disclaimer banner ── */}
      {!bannerDismissed && (
        <div
          style={{
            background: 'var(--surface-sunken)',
            border: '1px solid var(--border)',
            borderLeft: '3px solid var(--amber-500)',
            borderRadius: 'var(--radius-lg)',
            padding: 'var(--space-3) var(--space-4)',
            display: 'flex',
            gap: 'var(--space-3)',
            alignItems: 'flex-start',
          }}
        >
          <Info size={16} style={{ color: 'var(--amber-600)', flexShrink: 0, marginTop: '0.1rem' }} aria-hidden />
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-semibold)', color: 'var(--foreground)', marginBottom: '0.25rem' }}>
              Demo mode — Coach View
            </div>
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--muted-foreground)', margin: 0, lineHeight: 1.6 }}>
              In production this surface lives on a separate subdomain with coach-specific authentication and role-based access.
              It is a completely distinct AI system — its own knowledge graph, member context layer, and accountability engine —
              with no shared state with the athlete-facing app.
            </p>
          </div>
          <button
            type="button"
            className="ww-btn ww-btn--ghost ww-iconbtn ww-btn--sm"
            style={{ flexShrink: 0, color: 'var(--muted-foreground)' }}
            aria-label="Dismiss"
            onClick={() => { setBannerDismissed(true) }}
          >
            <X size={14} aria-hidden />
          </button>
        </div>
      )}

      {/* ── Page header ── */}
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-start', gap: 'var(--space-3)', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0 }}>Coach View</h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--muted-foreground)', margin: '0.25rem 0 0' }}>
            AI copilot for your 1:1 member session
          </p>
        </div>

        {/* ── Member switcher ── */}
        {members && members.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-1)', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--muted-foreground)', marginRight: 'var(--space-1)' }}>
              Member:
            </span>
            {members.map((m) => (
              <button
                key={m.member_id}
                type="button"
                className={`ww-btn ww-btn--sm${selectedMemberId === m.member_id ? '' : ' ww-btn--ghost'}`}
                style={{ fontSize: '0.75rem' }}
                onClick={() => { setSelectedMemberId(m.member_id) }}
                aria-pressed={selectedMemberId === m.member_id}
              >
                {m.member_name}
              </button>
            ))}
          </div>
        )}
      </div>

      {briefLoading && (
        <div style={{ color: 'var(--muted-foreground)', fontSize: '0.875rem' }}>
          Loading member context…
        </div>
      )}

      {briefError && (
        <div
          style={{
            background: 'var(--destructive)',
            color: 'var(--destructive-foreground)',
            borderRadius: '0.5rem',
            padding: 'var(--space-3)',
            fontSize: '0.875rem',
          }}
        >
          {briefError}
        </div>
      )}

      {brief && (
        <>
          {/* ── Member header card ── */}
          <div
            style={{
              background: 'var(--card)',
              border: '1px solid var(--border)',
              borderRadius: '0.75rem',
              padding: 'var(--space-4)',
              display: 'flex',
              flexWrap: 'wrap',
              gap: 'var(--space-4)',
              alignItems: 'flex-start',
              position: 'sticky',
              top: 0,
              zIndex: 10,
            }}
          >
            <div style={{ flex: 1, minWidth: '12rem' }}>
              <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>{brief.member_name}</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--muted-foreground)', marginTop: '0.15rem' }}>
                Age {brief.member_age} · {brief.tier}
              </div>
              <div style={{ marginTop: 'var(--space-2)', display: 'flex', flexWrap: 'wrap', gap: 'var(--space-1)' }}>
                {brief.goals
                  .sort((a: import('../types').GoalItem, b: import('../types').GoalItem) => a.priority - b.priority)
                  .map((g: import('../types').GoalItem) => (
                    <span
                      key={g.id}
                      className="ww-badge ww-badge--amber"
                    >
                      {g.text}
                    </span>
                  ))}
              </div>
            </div>

            {/* Churn risk */}
            <div
              style={{
                flexShrink: 0,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'flex-end',
                gap: 'var(--space-1)',
              }}
            >
              <div
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  color: churnColor,
                  border: `1px solid ${churnColor}`,
                  borderRadius: '999px',
                  padding: '0.2rem 0.7rem',
                }}
              >
                Churn risk: {churnLevel}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--muted-foreground)', textAlign: 'right', maxWidth: '16rem' }}>
                {brief.churn_risk.reasons[0]}
              </div>
            </div>
          </div>

          {/* ── Two-column: Morning brief + Adherence ── */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }} className="coach-grid">
            {/* Morning brief */}
            <div
              style={{
                background: 'var(--card)',
                border: '1px solid var(--border)',
                borderRadius: '0.75rem',
                padding: 'var(--space-4)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-3)',
              }}
            >
              <div style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--muted-foreground)' }}>
                Morning Brief
              </div>
              {brief.morning_tasks.map((task: import('../types').MorningTask, i: number) => (
                <div
                  key={i}
                  style={{
                    display: 'flex',
                    gap: 'var(--space-2)',
                    alignItems: 'flex-start',
                    background: 'var(--muted)',
                    borderRadius: '0.5rem',
                    padding: 'var(--space-3)',
                  }}
                >
                  {task.type === 'celebrate'
                    ? <PartyPopper size={18} strokeWidth={1.75} style={{ flexShrink: 0 }} />
                    : <AlertTriangle size={18} strokeWidth={1.75} style={{ flexShrink: 0 }} />}
                  <div>
                    <div style={{ fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', color: 'var(--muted-foreground)', marginBottom: '0.2rem' }}>
                      {task.type.replace('_', ' ')}
                    </div>
                    <div style={{ fontSize: '0.85rem', lineHeight: 1.4 }}>{task.text}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Adherence trend */}
            <div
              style={{
                background: 'var(--card)',
                border: '1px solid var(--border)',
                borderRadius: '0.75rem',
                padding: 'var(--space-4)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-3)',
              }}
            >
              <div style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--muted-foreground)' }}>
                Adherence — last 4 weeks
              </div>
              <AdherenceChart weeks={brief.adherence_weeks} />
              {brief.adherence_weeks.length > 1 && (
                <div style={{ fontSize: '0.75rem', color: 'var(--muted-foreground)' }}>
                  Trend:{' '}
                  {brief.adherence_weeks[brief.adherence_weeks.length - 1].pct <
                  brief.adherence_weeks[0].pct ? (
                    <span style={{ color: 'var(--destructive)', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                      <TrendingDown size={14} aria-hidden /> declining
                    </span>
                  ) : (
                    <span style={{ color: 'var(--success)', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                      <TrendingUp size={14} aria-hidden /> improving
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* ── Action Items ── */}
          <ActionItemsCard
            memberId={brief.member_id}
            memberName={brief.member_name}
            adherenceWeeks={brief.adherence_weeks}
            churnRisk={brief.churn_risk}
          />

          {selectedMemberId !== null && (
            <PendingDraftsPanel memberId={selectedMemberId} />
          )}

          {/* ── Message pattern + 4-week comparison ── */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }} className="coach-grid">
            {/* Message pattern chart */}
            <div
              style={{
                background: 'var(--card)',
                border: '1px solid var(--border)',
                borderRadius: '0.75rem',
                padding: 'var(--space-4)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-3)',
              }}
            >
              <div style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--muted-foreground)' }}>
                Message Pattern
              </div>
              {brief.message_pattern.length > 0 ? (
                <MessagePatternChart data={brief.message_pattern} />
              ) : (
                <div style={{ fontSize: '0.8rem', color: 'var(--muted-foreground)', padding: 'var(--space-3) 0' }}>
                  No message history yet.
                </div>
              )}
            </div>

            {/* 4-week comparison chart */}
            <div
              style={{
                background: 'var(--card)',
                border: '1px solid var(--border)',
                borderRadius: '0.75rem',
                padding: 'var(--space-4)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-3)',
              }}
            >
              <div style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--muted-foreground)' }}>
                Workouts vs Messages
              </div>
              {brief.weekly_comparison.length >= 1 ? (
                <WeeklyComparisonChart data={brief.weekly_comparison} />
              ) : (
                <div style={{ fontSize: '0.8rem', color: 'var(--muted-foreground)', padding: 'var(--space-3) 0' }}>
                  Not enough weekly data yet.
                </div>
              )}
            </div>
          </div>

          {/* ── Injury + equipment row ── */}
          {(brief.injuries.length > 0 || brief.equipment.length > 0) && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }} className="coach-grid">
              {brief.injuries.length > 0 && (
                <div
                  style={{
                    background: 'var(--card)',
                    border: '1px solid var(--border)',
                    borderRadius: '0.75rem',
                    padding: 'var(--space-4)',
                  }}
                >
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--muted-foreground)', marginBottom: 'var(--space-2)' }}>
                    Injuries
                  </div>
                  {brief.injuries.map((inj, i) => (
                    <div key={i} style={{ fontSize: '0.85rem', marginBottom: 'var(--space-2)' }}>
                      <div style={{ fontWeight: 600 }}>{inj.region} — <span style={{ textTransform: 'capitalize' }}>{inj.status}</span></div>
                      <div style={{ color: 'var(--muted-foreground)', fontSize: '0.8rem' }}>{inj.notes}</div>
                    </div>
                  ))}
                </div>
              )}
              {brief.equipment.length > 0 && (
                <div
                  style={{
                    background: 'var(--card)',
                    border: '1px solid var(--border)',
                    borderRadius: '0.75rem',
                    padding: 'var(--space-4)',
                  }}
                >
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--muted-foreground)', marginBottom: 'var(--space-2)' }}>
                    Equipment Available
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-1)' }}>
                    {brief.equipment.map((eq: string) => (
                      <span
                        key={eq}
                        style={{
                          fontSize: '0.75rem',
                          background: 'var(--muted)',
                          borderRadius: '0.25rem',
                          padding: '0.15rem 0.4rem',
                        }}
                      >
                        {eq}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* ── Coach copilot chat ── */}
      <div
        style={{
          background: 'var(--card)',
          border: '1px solid var(--border)',
          borderRadius: '0.75rem',
          padding: 'var(--space-4)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-3)',
          flex: 1,
          minHeight: '24rem',
        }}
      >
        <div style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--muted-foreground)' }}>
          Coach Copilot
        </div>

        {/* Quick-prompt chips */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-1)' }}>
          {QUICK_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              type="button"
              className="ww-btn ww-btn--ghost ww-btn--sm"
              style={{ fontSize: '0.75rem' }}
              disabled={chatLoading}
              onClick={() => { void handleSend(prompt) }}
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Message stream */}
        <div
          className="ww-scroll"
          style={{
            flex: 1,
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-2)',
            minHeight: '10rem',
            maxHeight: 'clamp(20rem, 45vh, 32rem)',
            padding: '0.25rem 0',
          }}
        >
          {messages.length === 0 && (
            <div style={{ color: 'var(--muted-foreground)', fontSize: '0.875rem', textAlign: 'center', marginTop: 'var(--space-4)' }}>
              Ask me anything about {brief?.member_name ?? 'your member'}'s progress, or click a quick-prompt above.
            </div>
          )}
          {messages.map((msg) => (
            <div key={msg.id}>
              <ChatBubble
                role={msg.role}
                content={msg.content}
                image={msg.image}
              />
              {msg.role === 'assistant' && msg.grounded_facts && msg.grounded_facts.length > 0 && (
                <div
                  style={{
                    marginTop: '0.25rem',
                    marginLeft: '0.5rem',
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: 'var(--space-1)',
                  }}
                >
                  {msg.grounded_facts.map((fact: string, i: number) => (
                    <span key={i} className="ww-badge ww-badge--amber">
                      {fact}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
          {chatLoading && <TypingBubble label="Thinking" />}
          {chatError && (
            <div style={{ color: 'var(--destructive)', fontSize: '0.875rem', padding: '0 0.5rem' }}>
              {chatError}
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Pending image preview */}
        {pendingImage && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-2)',
              padding: 'var(--space-2)',
              background: 'var(--muted)',
              borderRadius: '0.5rem',
              border: '1px solid var(--border)',
            }}
          >
            <img
              src={pendingImage}
              alt="Attachment preview"
              style={{
                maxHeight: '4rem',
                maxWidth: '8rem',
                borderRadius: '0.375rem',
                objectFit: 'cover',
              }}
            />
            <button
              type="button"
              className="ww-btn ww-btn--ghost ww-btn--sm"
              style={{ fontSize: '0.75rem', color: 'var(--muted-foreground)' }}
              onClick={() => { setPendingImage(null) }}
              aria-label="Remove image"
            >
              <X size={14} aria-hidden />
            </button>
          </div>
        )}

        {/* Input row */}
        <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'flex-end' }}>
          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            onChange={handleImageChange}
          />
          {/* Image attach trigger */}
          <button
            type="button"
            className="ww-btn ww-btn--ghost ww-btn--sm"
            style={{ flexShrink: 0, padding: '0.4rem 0.6rem' }}
            disabled={chatLoading}
            onClick={() => { fileInputRef.current?.click() }}
            aria-label="Attach image"
            title="Attach image"
          >
            <ImageIcon size={16} aria-hidden />
          </button>
          <textarea
            className="ww-scroll"
            style={{
              flex: 1,
              resize: 'none',
              minHeight: '2.5rem',
              maxHeight: '8rem',
              borderRadius: '0.5rem',
              border: '1px solid var(--border)',
              background: 'var(--background)',
              padding: '0.5rem 0.75rem',
              fontSize: '0.875rem',
              fontFamily: 'inherit',
              color: 'inherit',
              outline: 'none',
            }}
            placeholder={`Ask about ${brief?.member_name ?? 'your member'}'s adherence, sleep, goals…`}
            value={draft}
            rows={1}
            disabled={chatLoading}
            onChange={(e) => { setDraft(e.target.value) }}
            onKeyDown={handleKeyDown}
          />
          <button
            type="button"
            className="ww-btn ww-btn--gradient ww-btn--sm"
            disabled={chatLoading || (!draft.trim() && !pendingImage)}
            onClick={() => { void handleSend() }}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
