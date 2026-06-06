import { test, expect } from '@playwright/test'

function uniqueEmail() {
  return `test+${Date.now()}-${Math.random().toString(36).slice(2, 7)}@example.com`
}

const PASSWORD = 'TestPass123!'

test('register with new email → redirected to /workouts', async ({ page }) => {
  const email = uniqueEmail()
  await page.goto('/register')
  await page.fill('#email', email)
  await page.fill('#password', PASSWORD)
  await page.click('button[type="submit"]')
  await expect(page).toHaveURL('/workouts', { timeout: 10000 })
  await expect(page.getByText('My Workouts')).toBeVisible()
})

test('login with valid credentials → redirected to /workouts', async ({ page }) => {
  const email = uniqueEmail()
  // Register first
  await page.goto('/register')
  await page.fill('#email', email)
  await page.fill('#password', PASSWORD)
  await page.click('button[type="submit"]')
  await expect(page).toHaveURL('/workouts', { timeout: 10000 })

  // Logout
  await page.click('button:has-text("Logout")')
  await expect(page).toHaveURL('/login')

  // Login
  await page.fill('#email', email)
  await page.fill('#password', PASSWORD)
  await page.click('button[type="submit"]')
  await expect(page).toHaveURL('/workouts', { timeout: 10000 })
  await expect(page.getByText('My Workouts')).toBeVisible()
})

test('login with invalid password → error message shown', async ({ page }) => {
  const email = uniqueEmail()
  // Register first
  await page.goto('/register')
  await page.fill('#email', email)
  await page.fill('#password', PASSWORD)
  await page.click('button[type="submit"]')
  await expect(page).toHaveURL('/workouts', { timeout: 10000 })

  // Logout
  await page.click('button:has-text("Logout")')
  await expect(page).toHaveURL('/login')

  // Login with wrong password
  await page.fill('#email', email)
  await page.fill('#password', 'WrongPassword!')
  await page.click('button[type="submit"]')
  await expect(page.locator('.text-destructive')).toBeVisible({ timeout: 5000 })
  await expect(page).toHaveURL('/login')
})

test('logout → redirected to /login', async ({ page }) => {
  const email = uniqueEmail()
  await page.goto('/register')
  await page.fill('#email', email)
  await page.fill('#password', PASSWORD)
  await page.click('button[type="submit"]')
  await expect(page).toHaveURL('/workouts', { timeout: 10000 })

  await page.click('button:has-text("Logout")')
  await expect(page).toHaveURL('/login', { timeout: 5000 })
})

test('accessing /workouts without auth → redirected to /login', async ({ page }) => {
  // Clear storage to ensure no auth token
  await page.goto('/login')
  await page.evaluate(() => { localStorage.removeItem('auth_token'); })
  await page.goto('/workouts')
  await expect(page).toHaveURL('/login', { timeout: 5000 })
})
