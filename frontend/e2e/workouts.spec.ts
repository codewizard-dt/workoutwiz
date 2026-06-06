import { test, expect } from '@playwright/test'

function uniqueEmail() {
  return `test+${Date.now()}-${Math.random().toString(36).slice(2, 7)}@example.com`
}

const PASSWORD = 'TestPass123!'

async function registerAndLogin(page: import('@playwright/test').Page) {
  const email = uniqueEmail()
  await page.goto('/register')
  await page.fill('#email', email)
  await page.fill('#password', PASSWORD)
  await page.click('button[type="submit"]')
  await expect(page).toHaveURL('/workouts', { timeout: 10000 })
  return email
}

test('create a workout with one sequence and one set → workout appears in list', async ({ page }) => {
  await registerAndLogin(page)

  // Navigate to new workout form
  await page.click('a:has-text("New Workout")')
  await expect(page).toHaveURL('/workouts/new', { timeout: 5000 })

  // Add a sequence
  await page.click('button:has-text("+ Add Sequence")')
  // Wait for the sequence card to appear (contains "+ Add Set" button)
  await expect(page.locator('button:has-text("+ Add Set")')).toBeVisible({ timeout: 5000 })

  // Add a set within the sequence
  await page.click('button:has-text("+ Add Set")')

  // Select an exercise (first non-empty option)
  const exerciseSelect = page.locator('select').filter({ hasText: 'Select exercise…' }).first()
  await exerciseSelect.selectOption({ index: 1 })

  // Submit the form
  await page.click('button[type="submit"]:has-text("Save Workout")')
  await expect(page).toHaveURL('/workouts', { timeout: 10000 })

  // Workout should appear in the list — wait for it to be non-empty
  // The empty-state row has colSpan=4; a real workout row has individual cells
  await expect(page.locator('tbody tr td[colspan]')).toHaveCount(0, { timeout: 10000 })
  // Should show 1 sequence and 1 set
  await expect(page.locator('tbody tr').first().locator('td').nth(1)).toContainText('1')
  await expect(page.locator('tbody tr').first().locator('td').nth(2)).toContainText('1')
})

test('delete workout → it disappears from list', async ({ page }) => {
  await registerAndLogin(page)

  // Create a workout first
  await page.click('a:has-text("New Workout")')
  await page.click('button:has-text("+ Add Sequence")')
  await expect(page.locator('button:has-text("+ Add Set")')).toBeVisible({ timeout: 5000 })
  await page.click('button:has-text("+ Add Set")')
  const exerciseSelect = page.locator('select').filter({ hasText: 'Select exercise…' }).first()
  await exerciseSelect.selectOption({ index: 1 })
  await page.click('button[type="submit"]:has-text("Save Workout")')
  await expect(page).toHaveURL('/workouts', { timeout: 10000 })

  // Wait for the workout to appear (no empty-state colspan row)
  await expect(page.locator('tbody tr td[colspan]')).toHaveCount(0, { timeout: 10000 })

  // Delete it
  await page.click('button:has-text("Delete")')
  // After deletion, empty state message should appear
  await expect(page.getByText('No workouts yet.')).toBeVisible({ timeout: 10000 })
})
