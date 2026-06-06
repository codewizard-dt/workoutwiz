interface DeleteConfirmModalProps {
  open: boolean
  title: string
  description: string
  onConfirm: () => void
  onCancel: () => void
  loading?: boolean
}

export function DeleteConfirmModal({
  open,
  title,
  description,
  onConfirm,
  onCancel,
  loading = false,
}: DeleteConfirmModalProps) {
  if (!open) return null

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 50,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'oklch(0 0 0 / 0.45)',
      }}
      onClick={onCancel}
    >
      <div
        className="ww-card"
        style={{ width: 380, maxWidth: '90vw', padding: 'var(--space-5)' }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3
          style={{
            margin: '0 0 var(--space-2)',
            fontSize: 'var(--text-md)',
            fontWeight: 'var(--weight-semibold)',
            color: 'var(--destructive)',
          }}
        >
          {title}
        </h3>
        <p
          style={{
            margin: '0 0 var(--space-5)',
            fontSize: 'var(--text-sm)',
            color: 'var(--muted-foreground)',
            lineHeight: 1.5,
          }}
        >
          {description}
        </p>
        <div style={{ display: 'flex', gap: 'var(--space-2)', justifyContent: 'flex-end' }}>
          <button
            type="button"
            className="ww-btn ww-btn--outline"
            onClick={onCancel}
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="button"
            className="ww-btn ww-btn--destructive"
            onClick={onConfirm}
            disabled={loading}
          >
            {loading ? 'Deleting…' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  )
}
