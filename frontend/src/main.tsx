import './design-system/design-system.css'
import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { QueryCache, MutationCache, QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"
import { AuthProvider } from "@/context/AuthContext"
import { ApiError } from "@/lib/apiFetch"
import "./index.css"
import App from "./App.tsx"

/** Global guard: any 401 from a query or mutation clears the session and
 * redirects to login. Centralized here so no individual hook can forget it. */
function handleApiError(error: unknown) {
  if (error instanceof ApiError && error.status === 401) {
    window.dispatchEvent(new CustomEvent('ww:unauthorized'))
  }
}

const queryClient = new QueryClient({
  queryCache: new QueryCache({ onError: handleApiError }),
  mutationCache: new MutationCache({ onError: handleApiError }),
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      // Don't retry auth failures — a 401 won't fix itself on retry.
      retry: (failureCount, error) =>
        !(error instanceof ApiError && error.status === 401) && failureCount < 1,
    },
  },
})

const rootEl = document.getElementById("root")
if (!rootEl) throw new Error("Root element #root not found")
createRoot(rootEl).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <App />
      </AuthProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </StrictMode>,
)
