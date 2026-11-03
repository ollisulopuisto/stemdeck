import { test, expect } from '@playwright/test';

test('empty phone mixer exposes named transport and speed controls', async ({ page }) => {
  await page.goto('/?ui=mobile');
  await expect(page.getByRole('button', { name: 'Back to Library', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'More options', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Previous track', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Play', exact: true }).first()).toBeVisible();
  await expect(page.getByRole('button', { name: 'Next track', exact: true })).toBeVisible();
  await expect(page.getByRole('slider', { name: 'Playback speed', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Lower pitch', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Raise pitch', exact: true })).toBeVisible();
});
