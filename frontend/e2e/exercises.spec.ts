import { test, expect } from '@playwright/test'

test('navigate to /exercises → 50 exercises visible (no auth)', async ({ page }) => {
  await page.goto('/exercises')
  await expect(page.getByRole('heading', { name: 'Exercises' })).toBeVisible()
  // Wait for table to load (exercises are fetched from backend)
  await expect(page.locator('tbody tr')).toHaveCount(50, { timeout: 10000 })
})

test('search by name "squat" → results filtered', async ({ page }) => {
  await page.goto('/exercises')
  // Wait for initial load
  await expect(page.locator('tbody tr')).toHaveCount(50, { timeout: 10000 })

  await page.fill('#name-filter', 'squat')
  // Wait for debounce + re-fetch
  await expect(page.locator('tbody tr')).not.toHaveCount(50, { timeout: 5000 })
  // All visible rows should contain "squat" (case-insensitive)
  const rows = await page.locator('tbody tr td:first-child').allTextContents()
  for (const name of rows) {
    expect(name.toLowerCase()).toContain('squat')
  }
})

test('filter by muscle group "chest" → results filtered', async ({ page }) => {
  await page.goto('/exercises')
  await expect(page.locator('tbody tr')).toHaveCount(50, { timeout: 10000 })

  await page.fill('#muscle-filter', 'chest')
  await expect(page.locator('tbody tr')).not.toHaveCount(50, { timeout: 5000 })
  // Should have exactly 5 chest exercises (from seed data)
  await expect(page.locator('tbody tr')).toHaveCount(5, { timeout: 5000 })
})

test('clear filters → all 50 results visible again', async ({ page }) => {
  await page.goto('/exercises')
  await expect(page.locator('tbody tr')).toHaveCount(50, { timeout: 10000 })

  // Apply name filter
  await page.fill('#name-filter', 'squat')
  await expect(page.locator('tbody tr')).not.toHaveCount(50, { timeout: 5000 })

  // Clear filter
  await page.fill('#name-filter', '')
  await expect(page.locator('tbody tr')).toHaveCount(50, { timeout: 10000 })
})
