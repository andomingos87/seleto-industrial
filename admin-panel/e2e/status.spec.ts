import { test, expect } from '@playwright/test';
import { setupApiMocks, mockData, mockEndpoint } from './fixtures/api-mocks';

/**
 * E2E tests for Dashboard Status.
 * Tests integration status display, auto-refresh, and error states.
 * 
 * NOTE: These tests require authentication. Set E2E_TEST_EMAIL and E2E_TEST_PASSWORD
 * environment variables, or the tests will be skipped if redirected to login.
 */
test.describe('Dashboard Status', () => {
  test.beforeEach(async ({ page }) => {
    // Setup API mocks before each test
    await setupApiMocks(page);
    
    // Navigate to dashboard (status is now integrated into dashboard)
    await page.goto('/');
    
    // Check if we were redirected to login (not authenticated)
    if (page.url().includes('/login')) {
      test.skip(true, 'Not authenticated - set E2E_TEST_EMAIL and E2E_TEST_PASSWORD');
    }
  });

  test('should display dashboard with all integrations', async ({ page }) => {
    await page.goto('/');

    // Check page title
    await expect(page.locator('h1:has-text("Dashboard")')).toBeVisible();
    await expect(page.locator('text=Visão geral do SDR Agent')).toBeVisible();

    // Check all integration cards are present
    const integrations = ['WhatsApp', 'Supabase', 'OpenAI', 'PipeRun', 'Chatwoot'];
    for (const integration of integrations) {
      await expect(page.locator(`text=${integration}`).first()).toBeVisible();
    }
  });

  test('should display overall system status banner', async ({ page }) => {
    await page.goto('/');

    // Check for system status banner
    await expect(page.locator('text=Sistema Operacional')).toBeVisible();
    await expect(page.locator('text=ATIVO')).toBeVisible();
  });

  test('should show status indicators for each integration', async ({ page }) => {
    await page.goto('/');

    // Check for "Operacional" badges (all integrations are OK in mock)
    const operationalBadges = page.locator('text=Operacional');
    await expect(operationalBadges.first()).toBeVisible();
  });

  test('should have refresh button that works', async ({ page }) => {
    await page.goto('/');

    // Find and click refresh button
    const refreshButton = page.locator('button:has-text("Atualizar")');
    await expect(refreshButton).toBeVisible();

    // Click refresh
    await refreshButton.click();

    // Button should show loading state briefly
    // The page should still show the status after refresh
    await expect(page.locator('h1:has-text("Dashboard")')).toBeVisible();
  });

  test('should show auto-refresh indicator', async ({ page }) => {
    await page.goto('/');

    // Check for auto-refresh indicator
    await expect(page.locator('text=Auto-refresh a cada 30 segundos')).toBeVisible();
  });

  test('should display error state when API fails', async ({ page }) => {
    // Override mock to return error
    await mockEndpoint(page, '/api/admin/status', { error: 'Server error' }, 500);

    await page.goto('/');

    // Check for error message
    await expect(page.locator('text=Erro ao carregar status')).toBeVisible();
  });

  test('should show integration with error status correctly', async ({ page }) => {
    // Mock status with one integration in error
    const statusWithError = {
      ...mockData.status,
      agent_status: 'error',
      integrations: {
        ...mockData.status.integrations,
        piperun: { status: 'error', error: 'Connection timeout' },
      },
    };

    await mockEndpoint(page, '/api/admin/status', statusWithError);

    await page.goto('/');

    // Check for error status
    await expect(page.locator('text=Sistema com Problemas')).toBeVisible();
    // Use exact match for the ERRO badge
    await expect(page.getByText('ERRO', { exact: true })).toBeVisible();
  });

  test('should show warning status for unconfigured integrations', async ({ page }) => {
    // Mock status with warning
    const statusWithWarning = {
      ...mockData.status,
      integrations: {
        ...mockData.status.integrations,
        chatwoot: { status: 'warning', error: 'Not configured' },
      },
    };

    await mockEndpoint(page, '/api/admin/status', statusWithWarning);

    await page.goto('/');

    // Check for warning badge
    await expect(page.locator('text=Atenção').first()).toBeVisible();
  });

  test('should display latency values', async ({ page }) => {
    await page.goto('/');

    // Check for latency display (e.g., "120ms" for WhatsApp)
    await expect(page.locator('text=120ms').first()).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/');

    // Page should still be functional
    await expect(page.locator('h1:has-text("Dashboard")')).toBeVisible();

    // Integration cards should be visible (using data-slot attribute from shadcn)
    const cards = page.locator('[data-slot="card"]');
    await expect(cards.first()).toBeVisible();
  });

  test('should have quick actions with correct links', async ({ page }) => {
    await page.goto('/');

    // Check quick action buttons exist with correct links
    await expect(page.locator('a[href="/agent"]')).toBeVisible();
    await expect(page.locator('a[href="/leads"]')).toBeVisible();
    await expect(page.locator('a[href="/products"]')).toBeVisible();
    await expect(page.locator('a[href="/prompt"]')).toBeVisible();
    await expect(page.locator('a[href="/schedule"]')).toBeVisible();
    await expect(page.locator('a[href="/parameters"]')).toBeVisible();
    await expect(page.locator('a[href="/logs"]')).toBeVisible();
  });
});
