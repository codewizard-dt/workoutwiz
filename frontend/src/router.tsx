import { createBrowserRouter, Navigate } from 'react-router-dom'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'
import ExercisesPage from '@/pages/ExercisesPage'
import WorkoutsPage from '@/pages/WorkoutsPage'
import WorkoutNewPage from '@/pages/WorkoutNewPage'

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },
  { path: '/exercises', element: <ExercisesPage /> },
  { path: '/workouts', element: <ProtectedRoute><WorkoutsPage /></ProtectedRoute> },
  { path: '/workouts/new', element: <ProtectedRoute><WorkoutNewPage /></ProtectedRoute> },
  { path: '/', element: <Navigate to="/exercises" replace /> },
])
