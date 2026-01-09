import { test, expect } from '@playwright/test';
import { setupApiMocks, mockEndpoint, mockData } from './fixtures/api-mocks';

/**
 * E2E tests for Business Hours Configuration page.
 * Tests schedule editor, timezone selection, and save functionality.
 * 
 * NOTE: These tests require authentication. Set E2E_TEST_EMAIL and E2E_TEST_PASSWORD
 * environment variables, or the tests will be skipped if redirected to login.
 */
test.describe('Business Hours Configuration', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    
    // Navigate to schedule page (previously /agent/settings)
    await page.goto('/schedule');
    
    // Check if we were redirected to login (not authenticated)
    if (page.url().includes('/login')) {
      test.skip(true, 'Not authenticated - set E2E_TEST_EMAIL and E2E_TEST_PASSWORD');
    }
  });

  test('should display business hours page with correct elements', async ({ page }) => {
    // Check page title
    await expect(page.locator('h1:has-text("Horário de Funcionamento")')).toBeVisible();
    await expect(page.locator('text=Configure os horários de funcionamento')).toBeVisible();
  });

  test('should display current business hours status', async ({ page }) => {
    // Check for current status card - use first() to handle multiple matches
    await expect(page.locator('text=Dentro do Horário Comercial').first()).toBeVisible();
    await expect(page.getByText('ABERTO', { exact: true })).toBeVisible();
  });

  test('should display all days of the week', async ({ page }) => {
    await page.goto('/schedule');

    // Check all days are present
    const days = [
      'Segunda-feira',
      'Terça-feira',
      'Quarta-feira',
      'Quinta-feira',
      'Sexta-feira',
      'Sábado',
      'Domingo',
    ];

    for (const day of days) {
      await expect(page.locator(`text=${day}`)).toBeVisible();
    }
  });

  test('should show weekdays as enabled and weekends as disabled', async ({ page }) => {
    // Check that weekdays show "Aberto" badge (exact match to avoid ABERTO)
    const openBadges = page.getByText('Aberto', { exact: true });
    await expect(openBadges).toHaveCount(5); // Mon-Fri

    // Check that weekends show "Fechado" badge (exact match to avoid FECHADO)
    const closedBadges = page.getByText('Fechado', { exact: true });
    await expect(closedBadges).toHaveCount(2); // Sat-Sun
  });

  test('should allow toggling a day on/off', async ({ page }) => {
    await page.goto('/schedule');

    // Find the switch for Saturday (should be off)
    const switches = page.locator('button[role="switch"]');
    
    // Saturday is the 6th switch (0-indexed: 5)
    const saturdaySwitch = switches.nth(5);
    
    // Toggle it on
    await saturdaySwitch.click();

    // Should show "Alterações não salvas" badge
    await expect(page.locator('text=Alterações não salvas')).toBeVisible();
  });

  test('should allow changing time inputs', async ({ page }) => {
    await page.goto('/schedule');

    // Find time inputs for Monday
    const timeInputs = page.locator('input[type="time"]');
    
    // Change start time (first input)
    await timeInputs.first().fill('09:00');

    // Should show unsaved changes
    await expect(page.locator('text=Alterações não salvas')).toBeVisible();
  });

  test('should have timezone selector', async ({ page }) => {
    // Check for timezone section
    await expect(page.locator('text=Fuso Horário').first()).toBeVisible();

    // Check for timezone dropdown (contains São Paulo text)
    const timezoneSelect = page.locator('button').filter({ hasText: 'São Paulo' }).first();
    await expect(timezoneSelect).toBeVisible();
  });

  test('should allow changing timezone', async ({ page }) => {
    await page.goto('/schedule');

    // Click timezone dropdown
    await page.locator('button:has-text("São Paulo")').click();

    // Select different timezone
    await page.locator('text=Manaus').click();

    // Should show unsaved changes
    await expect(page.locator('text=Alterações não salvas')).toBeVisible();
  });

  test('should have save and discard buttons', async ({ page }) => {
    await page.goto('/schedule');

    // Check buttons exist
    await expect(page.locator('button:has-text("Salvar Alterações")')).toBeVisible();
    await expect(page.locator('button:has-text("Descartar")')).toBeVisible();

    // Buttons should be disabled when no changes
    await expect(page.locator('button:has-text("Salvar Alterações")')).toBeDisabled();
    await expect(page.locator('button:has-text("Descartar")')).toBeDisabled();
  });

  test('should enable save button after making changes', async ({ page }) => {
    await page.goto('/schedule');

    // Make a change
    const timeInputs = page.locator('input[type="time"]');
    await timeInputs.first().fill('09:00');

    // Save button should be enabled
    await expect(page.locator('button:has-text("Salvar Alterações")')).toBeEnabled();
  });

  test('should save changes successfully', async ({ page }) => {
    await page.goto('/schedule');

    // Make a change
    const timeInputs = page.locator('input[type="time"]');
    await timeInputs.first().fill('09:00');

    // Click save
    await page.locator('button:has-text("Salvar Alterações")').click();

    // Should show success toast
    await expect(page.locator('text=Horários salvos com sucesso')).toBeVisible({ timeout: 5000 });
  });

  test('should discard changes when clicking discard', async ({ page }) => {
    await page.goto('/schedule');

    // Make a change
    const timeInputs = page.locator('input[type="time"]');
    await timeInputs.first().fill('09:00');

    // Click discard
    await page.locator('button:has-text("Descartar")').click();

    // Unsaved changes badge should disappear
    await expect(page.locator('text=Alterações não salvas')).not.toBeVisible();
  });

  // Note: Closed status test removed - requires separate test context without beforeEach mocks
  // The closed status UI is tested via component tests

  // Note: API error test removed - requires separate test context without beforeEach mocks
  // The error handling is tested via unit tests in the backend

  test('should disable time inputs for closed days', async ({ page }) => {
    await page.goto('/schedule');

    // Find time inputs - Saturday and Sunday should have disabled inputs
    // There are 14 time inputs total (2 per day)
    const timeInputs = page.locator('input[type="time"]');
    
    // Saturday inputs (indices 10, 11) and Sunday inputs (indices 12, 13) should be disabled
    await expect(timeInputs.nth(10)).toBeDisabled();
    await expect(timeInputs.nth(11)).toBeDisabled();
    await expect(timeInputs.nth(12)).toBeDisabled();
    await expect(timeInputs.nth(13)).toBeDisabled();
  });
});
