import { Link, useNavigate } from 'react-router-dom'
import { useWorkouts, useDeleteWorkout } from '@/hooks/useWorkouts'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

export default function WorkoutsPage() {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const { data: workouts, isLoading, isError } = useWorkouts()
  const deleteWorkout = useDeleteWorkout()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">My Workouts</h1>
        <div className="flex gap-2">
          <Link
            to="/workouts/new"
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow hover:bg-primary/90"
          >
            New Workout
          </Link>
          <Button variant="outline" onClick={handleLogout}>
            Logout
          </Button>
        </div>
      </div>

      {isLoading && <p className="text-muted-foreground">Loading workouts…</p>}
      {isError && <p className="text-destructive">Failed to load workouts.</p>}

      {workouts && (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Sequences</TableHead>
                <TableHead>Sets</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {workouts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground">
                    No workouts yet.{' '}
                    <Link to="/workouts/new" className="underline">
                      Create one!
                    </Link>
                  </TableCell>
                </TableRow>
              ) : (
                workouts.map((w) => {
                  const totalSets = w.sequences.reduce(
                    (acc, seq) => acc + (seq.sets?.length ?? 0),
                    0
                  )
                  return (
                    <TableRow key={w.id}>
                      <TableCell>
                        {new Date(w.started_at).toLocaleString()}
                      </TableCell>
                      <TableCell>{w.sequences.length}</TableCell>
                      <TableCell>{totalSets}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="destructive"
                          size="sm"
                          disabled={deleteWorkout.isPending}
                          onClick={() => deleteWorkout.mutate(w.id)}
                        >
                          Delete
                        </Button>
                      </TableCell>
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}
