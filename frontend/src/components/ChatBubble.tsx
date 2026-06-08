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
  image?: string
}

export function ChatBubble({ role, content, route, confidence, steps, image }: ChatBubbleProps) {
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
          {image && (
            <div style={{ marginBottom: content ? 'var(--space-2)' : 0 }}>
              <img
                src={image}
                alt="Attached image"
                style={{
                  maxWidth: '100%',
                  maxHeight: '16rem',
                  borderRadius: '0.5rem',
                  border: '1px solid var(--border)',
                  display: 'block',
                  objectFit: 'contain',
                }}
              />
            </div>
          )}
          {content && (
            <div style={{ lineHeight: 1.55 }} className="markdown-content">
              {isUser ? content : <ReactMarkdown>{content}</ReactMarkdown>}
            </div>
          )}
          {!isUser && steps && steps.length > 0 && (
            <AgentTrace steps={steps} />
          )}
        </div>
      </div>
    </div>
  )
}
