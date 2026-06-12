import { test, expect } from '@playwright/test'

const CARD = '[data-testid="exercise-card"]'

test.beforeEach(async ({ page, request }) => {
  const res = await request.post('/api/auth/jwt/login', {
    form: { username: 'alex@example.com', password: 'password123' },
  })
  const { access_token } = (await res.json()) as { access_token: string }
  await page.addInitScript((token) => {
    localStorage.setItem('auth_token', token)
  }, access_token)
})

test('navigate to /exercises → 50 exercise cards visible', async ({ page }) => {
  await page.goto('/exercises')
  await expect(page.getByRole('heading', { name: 'Exercises' })).toBeVisible()
  await expect(page.locator(CARD)).toHaveCount(50, { timeout: 10000 })
})

test('search by name "squat" → cards filtered', async ({ page }) => {
  await page.goto('/exercises')
  await expect(page.locator(CARD)).toHaveCount(50, { timeout: 10000 })

  await page.fill('#name-filter', 'squat')
  await expect(page.locator(CARD)).not.toHaveCount(50, { timeout: 5000 })

  const names = await page.locator(`${CARD} h3`).allTextContents()
  expect(names.length).toBeGreaterThan(0)
  for (const name of names) {
    expect(name.toLowerCase()).toContain('squat')
  }
})

test('filter by muscle group chip "chest" → 5 cards', async ({ page }) => {
  await page.goto('/exercises')
  await expect(page.locator(CARD)).toHaveCount(50, { timeout: 10000 })

  await page.getByRole('button', { name: 'chest', exact: true }).click()
  await expect(page.locator(CARD)).toHaveCount(5, { timeout: 5000 })
})

test('clear all → 50 cards visible again', async ({ page }) => {
  await page.goto('/exercises')
  await expect(page.locator(CARD)).toHaveCount(50, { timeout: 10000 })

  await page.fill('#name-filter', 'squat')
  await expect(page.locator(CARD)).not.toHaveCount(50, { timeout: 5000 })

  await page.getByRole('button', { name: 'Clear all' }).click()
  await expect(page.locator(CARD)).toHaveCount(50, { timeout: 10000 })
})

test('clicking a card opens the detail drawer', async ({ page }) => {
  await page.goto('/exercises')
  await expect(page.locator(CARD)).toHaveCount(50, { timeout: 10000 })

  await page.locator(CARD).first().click()
  await expect(page.getByRole('dialog')).toBeVisible()
})

test('toggling the Safe-for-me lens sets aria-pressed', async ({ page }) => {
  await page.goto('/exercises')
  await expect(page.locator(CARD)).toHaveCount(50, { timeout: 10000 })

  await page.getByTestId('safety-lens-toggle').click()
  await expect(page.getByTestId('safety-lens-toggle')).toHaveAttribute('aria-pressed', 'true')
})
