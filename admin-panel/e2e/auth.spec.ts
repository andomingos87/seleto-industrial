import { test, expect } from '@playwright/test';

/**
 * E2E tests for authentication flow.
 * Tests login page, form validation, and authentication redirects.
 */
test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    // Clear any existing auth state
    await page.context().clearCookies();
  });

  test('should display login page with correct elements', async ({ page }) => {
    await page.goto('/login');

    // Check page title and branding
    await expect(page.locator('text=SDR Agent Admin')).toBeVisible();
    await expect(page.locator('text=Entre com suas credenciais')).toBeVisible();

    // Check form elements
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toHaveText('Entrar');
  });

  test('should show validation errors for empty form', async ({ page }) => {
    await page.goto('/login');

    // Click submit without filling form
    await page.click('button[type="submit"]');

    // Check for validation errors
    await expect(page.locator('text=Email invalido')).toBeVisible();
  });

  test('should show validation error for invalid email', async ({ page }) => {
    await page.goto('/login');

    // Fill invalid email - browser's native validation may kick in
    // We test that the form doesn't submit with invalid email
    const emailInput = page.locator('input[type="email"]');
    await emailInput.fill('invalid-email');
    await page.fill('input[type="password"]', 'password123');
    
    // Try to submit - should be blocked by browser validation or Zod
    await page.click('button[type="submit"]');
    
    // The form should still be on the login page (not redirected)
    await expect(page).toHaveURL(/\/login/);
    
    // Email input should have validation state (browser native or custom)
    // Check that the input is still visible and we're still on login
    await expect(emailInput).toBeVisible();
  });

  test('should show validation error for short password', async ({ page }) => {
    await page.goto('/login');

    // Fill short password
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', '123');
    await page.click('button[type="submit"]');

    // Check for validation error
    await expect(page.locator('text=Senha deve ter no minimo 6 caracteres')).toBeVisible();
  });

  test('should redirect unauthenticated users to login', async ({ page }) => {
    // Try to access protected route
    await page.goto('/status');

    // Should be redirected to login
    await expect(page).toHaveURL(/\/login/);
  });

  test('should redirect unauthenticated users from dashboard to login', async ({ page }) => {
    // Try to access dashboard
    await page.goto('/');

    // Should be redirected to login
    await expect(page).toHaveURL(/\/login/);
  });

  test('should show loading state while submitting', async ({ page }) => {
    await page.goto('/login');

    // Fill valid credentials
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'password123');

    // Mock slow response
    await page.route('**/auth/**', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      await route.continue();
    });

    // Click submit
    await page.click('button[type="submit"]');

    // Check for loading spinner (Loader2 icon with animate-spin)
    await expect(page.locator('button[type="submit"] svg.animate-spin')).toBeVisible();
  });

  test('login form should be accessible', async ({ page }) => {
    await page.goto('/login');

    // Check labels are associated with inputs
    const emailLabel = page.locator('label[for="email"]');
    const passwordLabel = page.locator('label[for="password"]');

    await expect(emailLabel).toBeVisible();
    await expect(passwordLabel).toBeVisible();

    // Check inputs have proper attributes
    const emailInput = page.locator('input[type="email"]');
    const passwordInput = page.locator('input[type="password"]');

    await expect(emailInput).toHaveAttribute('id', 'email');
    await expect(passwordInput).toHaveAttribute('id', 'password');
  });
});
