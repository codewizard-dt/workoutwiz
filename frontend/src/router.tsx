import { createBrowserRouter, Navigate } from 'react-router-dom'
import LandingPage from '@/pages/LandingPage'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'
import ExercisesPage from '@/pages/ExercisesPage'
import WorkoutsPage from '@/pages/WorkoutsPage'
import WorkoutNewPage from '@/pages/WorkoutNewPage'
import ChatPage from '@/pages/ChatPage'
import WorkoutDetailPage from '@/pages/WorkoutDetailPage'
import { AppShell } from '@/components/AppShell'

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },
  {
    path: '/exercises',
    element: (
      <ProtectedRoute>
        <AppShell><ExercisesPage /></AppShell>
      </ProtectedRoute>
    ),
  },
  {
    path: '/chat',
    element: (
      <ProtectedRoute>
        <AppShell><ChatPage /></AppShell>
      </ProtectedRoute>
    ),
  },
  {
    path: '/workouts',
    element: (
      <ProtectedRoute>
        <AppShell><WorkoutsPage /></AppShell>
      </ProtectedRoute>
    ),
  },
  {
    path: '/workouts/new',
    element: (
      <ProtectedRoute>
        <AppShell><WorkoutNewPage /></AppShell>
      </ProtectedRoute>
    ),
  },
  {
    path: '/workouts/:workoutId',
    element: (
      <ProtectedRoute>
        <AppShell><WorkoutDetailPage /></AppShell>
      </ProtectedRoute>
    ),
  },
  { path: '/knowledge-graph', element: <Navigate to="/chat" replace /> },
  { path: '/', element: <LandingPage /> },
])
