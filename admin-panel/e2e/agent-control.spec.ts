import { test, expect } from '@playwright/test';
import { setupApiMocks, mockEndpoint } from './fixtures/api-mocks';

/**
 * E2E tests for Agent Control page.
 * Tests pause/resume functionality, phone management, and prompt reload.
 * 
 * NOTE: These tests require authentication. Set E2E_TEST_EMAIL and E2E_TEST_PASSWORD
 * environment variables, or the tests will be skipped if redirected to login.
 */
test.describe('Agent Control', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    
    // Navigate to agent page
    await page.goto('/agent');
    
    // Check if we were redirected to login (not authenticated)
    if (page.url().includes('/login')) {
      test.skip(true, 'Not authenticated - set E2E_TEST_EMAIL and E2E_TEST_PASSWORD');
    }
  });

  test('should display agent control page with correct elements', async ({ page }) => {
    // Check page title
    await expect(page.locator('h1:has-text("Controle do Agente")')).toBeVisible();
    await expect(page.locator('text=Gerencie o status e operação do agente SDR')).toBeVisible();

    // Check main sections
    await expect(page.locator('text=Status Global').first()).toBeVisible();
    await expect(page.locator('text=Telefones Pausados').first()).toBeVisible();
  });

  test('should display current agent status', async ({ page }) => {
    await page.goto('/agent');

    // Check status badge
    await expect(page.locator('text=Status Atual')).toBeVisible();
    await expect(page.locator('text=Ativo')).toBeVisible();
  });

  test('should display count of paused phones', async ({ page }) => {
    await page.goto('/agent');

    // Check paused phones count (mock has 1 paused phone)
    await expect(page.locator('text=Telefones Pausados').first()).toBeVisible();
    // The badge should show "1"
    const badge = page.locator('text=1').first();
    await expect(badge).toBeVisible();
  });

  test('should display list of paused phones', async ({ page }) => {
    await page.goto('/agent');

    // Check for the paused phone number in the list
    // The mock has 5511999999999 as paused
    await expect(page.locator('text=+55 (11) 99999-9999')).toBeVisible();
  });

  test('should allow adding a phone to pause list', async ({ page }) => {
    // Find the phone input
    const phoneInput = page.locator('input[placeholder="5511999999999"]');
    await expect(phoneInput).toBeVisible();

    // Enter a phone number
    await phoneInput.fill('5521988888888');

    // Click add button (the Plus icon button next to input)
    const addButton = page.locator('button').filter({ has: page.locator('svg.lucide-plus') });
    await addButton.click();

    // Should show success toast (contains "Agent paused" or similar success message)
    await expect(page.locator('[data-sonner-toast]').first()).toBeVisible({ timeout: 5000 });
  });

  test('should show error when trying to pause without phone', async ({ page }) => {
    await page.goto('/agent');

    // Try to add without entering phone
    const phoneInput = page.locator('input[placeholder="5511999999999"]');
    await phoneInput.fill('');

    // The add button should be disabled when input is empty
    const addButton = page.locator('button:has(svg.lucide-plus)');
    await expect(addButton).toBeDisabled();
  });

  test('should allow resuming a paused phone', async ({ page }) => {
    // Wait for the page to fully load
    await page.waitForLoadState('networkidle');
    
    // Find the resume button (Play icon) for the paused phone
    const resumeButton = page.locator('button').filter({ has: page.locator('svg.lucide-play') }).first();
    await expect(resumeButton).toBeVisible();
    await expect(resumeButton).toBeEnabled({ timeout: 5000 });

    // Click resume
    await resumeButton.click();

    // Should show success toast
    await expect(page.locator('[data-sonner-toast]').first()).toBeVisible({ timeout: 5000 });
  });

  test('should have reload prompt button with confirmation', async ({ page }) => {
    // Find reload prompt button
    const reloadButton = page.locator('button:has-text("Recarregar Prompt")');
    await expect(reloadButton).toBeVisible();

    // Click to open confirmation dialog
    await reloadButton.click();

    // Check confirmation dialog
    await expect(page.locator('text=Recarregar System Prompt?')).toBeVisible();
    await expect(page.locator('text=sp_agente_v1.xml')).toBeVisible();

    // Confirm reload (click the action button in the dialog)
    await page.locator('[role="alertdialog"] button:has-text("Recarregar")').click();

    // Should show success toast
    await expect(page.locator('[data-sonner-toast]').first()).toBeVisible({ timeout: 5000 });
  });

  test('should show global pause/resume buttons as disabled', async ({ page }) => {
    await page.goto('/agent');

    // Check that global buttons are disabled (not implemented)
    const pauseAllButton = page.locator('button:has-text("Pausar Todos")');
    const resumeAllButton = page.locator('button:has-text("Retomar Todos")');

    await expect(pauseAllButton).toBeDisabled();
    await expect(resumeAllButton).toBeDisabled();

    // Check for "versão futura" message
    await expect(page.locator('text=versão futura')).toBeVisible();
  });

  // Note: API error test removed - requires separate test context without beforeEach mocks
  // The error handling is tested via unit tests in the backend

  test('should format phone numbers correctly', async ({ page }) => {
    await page.goto('/agent');

    // The mock has 5511999999999 which should be formatted as +55 (11) 99999-9999
    await expect(page.locator('text=+55 (11) 99999-9999')).toBeVisible();
  });
});
