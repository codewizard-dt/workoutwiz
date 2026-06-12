import { test, expect } from '@playwright/test'

test('coach page shows morning brief for logged-in coach', async ({ page }) => {
  // Log in as demo coach
  await page.goto('/login')
  await page.fill('#email', 'alex@example.com')
  await page.fill('#password', 'password123')
  await page.click('button[type="submit"]')
  await expect(page).toHaveURL('/chat', { timeout: 10000 })

  // Navigate to coach page
  await page.goto('/coach')

  // Wait for morning brief section to load (Alex Chen is the member for the demo coach)
  await expect(page.getByText('Alex Chen')).toBeVisible({ timeout: 15000 })

  // The Morning Brief section must be visible
  const morningBrief = page.getByText('Morning Brief', { exact: true })
  await expect(morningBrief).toBeVisible()

  // If action items are present, the card heading must be visible too
  const actionItemsCard = page.getByText('Action Items', { exact: true })
  const actionItemsCount = await actionItemsCard.count()
  if (actionItemsCount > 0) {
    await expect(actionItemsCard).toBeVisible()
  }
})
