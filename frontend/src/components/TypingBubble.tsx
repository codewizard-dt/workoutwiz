export function TypingBubble({ label = 'Thinking' }: { label?: string }) {
  return (
    <div className="ww-chat ww-chat--coach">
      <div className="ww-chat__body">
        <div className="ww-typing-bubble" role="status" aria-label={label}>
          <span className="ww-typing-bubble__dot" />
          <span className="ww-typing-bubble__dot" />
          <span className="ww-typing-bubble__dot" />
        </div>
      </div>
    </div>
  )
}
