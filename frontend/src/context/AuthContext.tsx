import { createContext, useContext, useState } from "react"
import type { ReactNode } from "react"

interface AuthContextValue {
  token: string | null
  setToken: (token: string | null) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(
    () => localStorage.getItem("auth_token")
  )

  const setToken = (t: string | null) => {
    setTokenState(t)
    if (t) localStorage.setItem("auth_token", t)
    else localStorage.removeItem("auth_token")
  }

  const logout = () => { setToken(null); }

  return <AuthContext.Provider value={{ token, setToken, logout }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
