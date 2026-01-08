import { test as base, expect, Page } from '@playwright/test';

/**
 * Test credentials for E2E tests.
 * In CI, these should be set via environment variables.
 */
const TEST_USER = {
  email: process.env.E2E_TEST_EMAIL || 'test@seleto.com.br',
  password: process.env.E2E_TEST_PASSWORD || 'test123456',
};

/**
 * Extended test fixture with authentication helpers.
 */
export const test = base.extend<{
  authenticatedPage: Page;
}>({
  authenticatedPage: async ({ page }, use) => {
    // Navigate to login page
    await page.goto('/login');
    
    // Wait for the page to load
    await page.waitForSelector('input[type="email"]');
    
    // Fill in credentials
    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    
    // Click login button
    await page.click('button[type="submit"]');
    
    // Wait for redirect to dashboard
    await page.waitForURL('/', { timeout: 10000 });
    
    // Use the authenticated page
    await use(page);
  },
});

export { expect };

/**
 * Helper to login programmatically.
 */
export async function login(page: Page, email?: string, password?: string) {
  await page.goto('/login');
  await page.waitForSelector('input[type="email"]');
  
  await page.fill('input[type="email"]', email || TEST_USER.email);
  await page.fill('input[type="password"]', password || TEST_USER.password);
  
  await page.click('button[type="submit"]');
  await page.waitForURL('/', { timeout: 10000 });
}

/**
 * Helper to check if user is authenticated.
 */
export async function isAuthenticated(page: Page): Promise<boolean> {
  const url = page.url();
  return !url.includes('/login');
}
