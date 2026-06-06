import ReactMarkdown from 'react-markdown'
import { cn } from '@/lib/utils'
import { RouteBadge } from './RouteBadge'
import { AgentTrace, type AgentStep } from './AgentTrace'

interface ChatBubbleProps {
  role: 'user' | 'assistant'
  content: string
  route?: string
  confidence?: number
  steps?: AgentStep[]
}

export function ChatBubble({ role, content, route, confidence, steps }: ChatBubbleProps) {
  const isUser = role === 'user'

  return (
    <div className={cn('ww-chat', isUser ? 'ww-chat--user' : 'ww-chat--coach')}>
      <div className="ww-chat__body">
        <div className={cn('ww-chat__bubble', isUser ? 'ww-chat-bubble--user' : 'ww-chat-bubble--coach')}>
          {!isUser && route && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-2)',
                flexWrap: 'wrap',
                marginBottom: 'var(--space-2)',
              }}
            >
              <RouteBadge route={route} confidence={confidence} />
            </div>
          )}
          <div style={{ lineHeight: 1.55 }} className="markdown-content">
            {isUser ? content : <ReactMarkdown>{content}</ReactMarkdown>}
          </div>
          {!isUser && steps && steps.length > 0 && (
            <AgentTrace steps={steps} />
          )}
        </div>
      </div>
    </div>
  )
}
