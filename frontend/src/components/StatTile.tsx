import type { ReactNode } from 'react'

interface StatTileProps {
  label: string
  value: ReactNode
  icon?: ReactNode
}

/**
 * A single dashboard stat tile (label + large mono value), wrapping the
 * `.ww-stat` design-system primitive. Numerics render in the mono face via
 * `.ww-stat__value`.
 */
export function StatTile({ label, value, icon }: StatTileProps) {
  return (
    <div className="ww-stat">
      <span className="ww-stat__label">
        {icon}
        {label}
      </span>
      <span className="ww-stat__value">{value}</span>
    </div>
  )
}
