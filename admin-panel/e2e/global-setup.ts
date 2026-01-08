import { chromium, FullConfig } from '@playwright/test';

/**
 * Global setup for E2E tests.
 * Performs login and saves authentication state for reuse in tests.
 */
async function globalSetup(config: FullConfig) {
  const { baseURL } = config.projects[0].use;
  
  // Check if we have test credentials
  const email = process.env.E2E_TEST_EMAIL;
  const password = process.env.E2E_TEST_PASSWORD;
  
  if (!email || !password) {
    console.log('⚠️  E2E_TEST_EMAIL and E2E_TEST_PASSWORD not set.');
    console.log('   Protected page tests will be skipped or may fail.');
    console.log('   Set these environment variables to run full E2E tests.');
    return;
  }

  console.log('🔐 Setting up authentication...');
  
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navigate to login page
    await page.goto(`${baseURL}/login`, { waitUntil: 'networkidle' });
    
    // Wait for the page to load
    await page.waitForSelector('input[type="email"]', { timeout: 15000 });
    
    console.log('📝 Filling credentials...');
    
    // Fill in credentials
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', password);
    
    // Click login button
    await page.click('button[type="submit"]');
    
    // Wait for redirect - check that we're no longer on login page
    await page.waitForURL((url) => !url.pathname.includes('/login'), { 
      timeout: 20000,
      waitUntil: 'domcontentloaded'
    });
    
    // Give it a moment to settle
    await page.waitForTimeout(1000);
    
    console.log('✅ Authentication successful! Current URL:', page.url());
    
    // Save authentication state
    await context.storageState({ path: 'e2e/.auth/user.json' });
    console.log('💾 Auth state saved to e2e/.auth/user.json');
    
  } catch (error) {
    console.error('❌ Authentication failed:', error);
    console.log('   Current URL:', page.url());
    console.log('   Protected page tests may fail.');
  } finally {
    await browser.close();
  }
}

export default globalSetup;
