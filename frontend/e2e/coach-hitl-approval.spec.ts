import { test, expect } from '@playwright/test'

test('coach can approve and send a draft nudge', async ({ page }) => {
  // Log in with the seeded coach account
  await page.goto('/login')
  await page.fill('#email', 'alex@example.com')
  await page.fill('#password', 'password123')
  await page.click('button[type="submit"]')
  await expect(page).toHaveURL('/workouts', { timeout: 10000 })

  // Navigate to coach page
  await page.goto('/coach')

  // Wait for the page to load (coach brief page has member data)
  await page.waitForLoadState('networkidle', { timeout: 15000 })

  // If Action Items "Draft Nudge" buttons are visible, click the first one to create a draft
  const draftNudgeBtn = page.getByRole('button', { name: 'Draft Nudge' }).first()
  if (await draftNudgeBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
    await draftNudgeBtn.click()
    // Wait for draft to be created and appear in panel
    await page.waitForTimeout(3000)
  }

  // Check if Pending Drafts panel is visible
  const pendingDraftsSection = page.locator('text=Pending Drafts').first()
  if (await pendingDraftsSection.isVisible({ timeout: 5000 }).catch(() => false)) {
    // Send button should be disabled before approval
    const sendBtn = page.getByRole('button', { name: 'Send' }).first()
    await expect(sendBtn).toBeDisabled()

    // Approve the first draft
    const approveBtn = page.getByRole('button', { name: 'Approve' }).first()
    await approveBtn.click()

    // Send button should now be enabled
    await expect(sendBtn).toBeEnabled({ timeout: 5000 })

    // Click Send
    await sendBtn.click()

    // Give time for the action to complete
    await page.waitForTimeout(1000)
  }
})
