import { useState, useEffect } from 'react'
import { useExercises } from '@/hooks/useExercises'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(t)
  }, [value, delay])
  return debounced
}

export default function ExercisesPage() {
  const [nameInput, setNameInput] = useState('')
  const [muscleInput, setMuscleInput] = useState('')
  const [equipmentInput, setEquipmentInput] = useState('')

  const debouncedName = useDebounce(nameInput, 300)
  const debouncedMuscle = useDebounce(muscleInput, 300)
  const debouncedEquipment = useDebounce(equipmentInput, 300)

  const filters = {
    name: debouncedName || undefined,
    muscle_groups: debouncedMuscle
      ? debouncedMuscle.split(',').map((s) => s.trim()).filter(Boolean)
      : undefined,
    equipment: debouncedEquipment
      ? debouncedEquipment.split(',').map((s) => s.trim()).filter(Boolean)
      : undefined,
  }

  const { data: exercises, isLoading, isError } = useExercises(filters)

  return (
    <div className="container mx-auto py-8 space-y-6">
      <h1 className="text-3xl font-bold">Exercises</h1>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="space-y-1">
          <Label htmlFor="name-filter">Name</Label>
          <Input
            id="name-filter"
            placeholder="Search by name…"
            value={nameInput}
            onChange={(e) => setNameInput(e.target.value)}
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="muscle-filter">Muscle groups (comma-separated)</Label>
          <Input
            id="muscle-filter"
            placeholder="e.g. chest, triceps"
            value={muscleInput}
            onChange={(e) => setMuscleInput(e.target.value)}
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="equipment-filter">Equipment (comma-separated)</Label>
          <Input
            id="equipment-filter"
            placeholder="e.g. barbell, dumbbell"
            value={equipmentInput}
            onChange={(e) => setEquipmentInput(e.target.value)}
          />
        </div>
      </div>

      {isLoading && <p className="text-muted-foreground">Loading exercises…</p>}
      {isError && <p className="text-destructive">Failed to load exercises.</p>}

      {exercises && (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Muscle Groups</TableHead>
                <TableHead>Equipment</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {exercises.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground">
                    No exercises found.
                  </TableCell>
                </TableRow>
              ) : (
                exercises.map((ex) => (
                  <TableRow key={ex.id}>
                    <TableCell className="font-medium">{ex.name}</TableCell>
                    <TableCell>{ex.category ?? '—'}</TableCell>
                    <TableCell>{ex.muscle_groups.join(', ') || '—'}</TableCell>
                    <TableCell>{ex.equipment_required.join(', ') || '—'}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}
