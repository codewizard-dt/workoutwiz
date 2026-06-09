/** Error thrown by {@link apiFetch} for any non-2xx response. Carries the HTTP
 * status so global handlers (e.g. the TanStack QueryClient caches) can react to
 * specific codes such as 401. */
export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message || `Request failed with status ${status}`)
    this.name = 'ApiError'
    this.status = status
  }
}

/** The single fetch transport for the app. Throws {@link ApiError} on any
 * non-OK response so errors carry their HTTP status; on success returns the raw
 * Response. Every query/mutation should call this (never `fetch` directly) so
 * the global 401 guard wired into the QueryClient always applies. */
export async function apiFetch(url: string, options?: RequestInit): Promise<Response> {
  const res = await fetch(url, options)
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new ApiError(res.status, body)
  }
  return res
}
