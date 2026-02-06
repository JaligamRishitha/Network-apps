/**
 * Browser Automation Test for SAP ERP Frontend
 * Tests all pages and functionality using Playwright
 */
const { chromium } = require('playwright');

const BASE_URL = 'http://localhost:2003';
const API_URL = 'http://localhost:2004';

// Test results tracking
const results = {
  passed: [],
  failed: [],
  screenshots: []
};

function log(message, type = 'INFO') {
  const timestamp = new Date().toISOString().substr(11, 8);
  const prefix = type === 'PASS' ? '✅' : type === 'FAIL' ? '❌' : type === 'WARN' ? '⚠️' : 'ℹ️';
  console.log(`[${timestamp}] ${prefix} ${message}`);
}

async function takeScreenshot(page, name) {
  const filename = `test-screenshots/${name.replace(/\s+/g, '-').toLowerCase()}.png`;
  try {
    await page.screenshot({ path: filename, fullPage: true });
    results.screenshots.push(filename);
    log(`Screenshot saved: ${filename}`);
  } catch (e) {
    log(`Failed to save screenshot: ${e.message}`, 'WARN');
  }
}

async function testLogin(page) {
  log('=== Testing Login Page ===');

  try {
    await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);

    // Check login form exists
    const usernameInput = await page.$('input[type="text"], input[name="username"]');
    const passwordInput = await page.$('input[type="password"]');
    const loginButton = await page.$('button[type="submit"], button:has-text("Login"), button:has-text("Sign")');

    if (!usernameInput || !passwordInput) {
      throw new Error('Login form inputs not found');
    }

    await takeScreenshot(page, '01-login-page');

    // Fill login form
    await usernameInput.fill('admin');
    await passwordInput.fill('admin123');
    await takeScreenshot(page, '02-login-filled');

    // Click login
    if (loginButton) {
      await loginButton.click();
    } else {
      await page.keyboard.press('Enter');
    }

    // Wait for navigation
    await page.waitForTimeout(2000);

    // Check if logged in (should redirect away from login)
    const currentUrl = page.url();
    if (!currentUrl.includes('/login')) {
      results.passed.push('Login functionality');
      log('Login successful', 'PASS');
      await takeScreenshot(page, '03-after-login');
      return true;
    } else {
      throw new Error('Still on login page after login attempt');
    }
  } catch (error) {
    results.failed.push(`Login: ${error.message}`);
    log(`Login failed: ${error.message}`, 'FAIL');
    await takeScreenshot(page, '03-login-error');
    return false;
  }
}

async function testNavigation(page) {
  log('=== Testing Navigation ===');

  const navItems = [
    { name: 'Dashboard/Home', selectors: ['a:has-text("Dashboard")', 'a:has-text("Home")', '[href="/"]', '[href="/dashboard"]'] },
    { name: 'PM Module', selectors: ['a:has-text("PM")', 'a:has-text("Plant")', '[href="/pm"]'] },
    { name: 'MM Module', selectors: ['a:has-text("MM")', 'a:has-text("Material")', '[href="/mm"]'] },
    { name: 'FI Module', selectors: ['a:has-text("FI")', 'a:has-text("Finance")', '[href="/fi"]'] },
    { name: 'Tickets', selectors: ['a:has-text("Ticket")', '[href*="ticket"]'] },
  ];

  for (const nav of navItems) {
    try {
      let clicked = false;
      for (const selector of nav.selectors) {
        const element = await page.$(selector);
        if (element) {
          await element.click();
          clicked = true;
          break;
        }
      }

      if (clicked) {
        await page.waitForTimeout(1500);
        results.passed.push(`Navigation: ${nav.name}`);
        log(`Navigation to ${nav.name} works`, 'PASS');
      } else {
        log(`Navigation ${nav.name} not found`, 'WARN');
      }
    } catch (error) {
      log(`Navigation ${nav.name}: ${error.message}`, 'WARN');
    }
  }
}

async function testPMModule(page) {
  log('=== Testing PM (Plant Maintenance) Module ===');

  try {
    // Navigate to PM
    await page.goto(`${BASE_URL}/pm`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    await takeScreenshot(page, '10-pm-page');

    // Check for data tables or lists
    const tables = await page.$$('table, [role="grid"], .MuiTable-root, .data-table');
    const lists = await page.$$('ul, ol, .list, .MuiList-root');

    if (tables.length > 0 || lists.length > 0) {
      results.passed.push('PM Module: Data displayed');
      log('PM data tables/lists found', 'PASS');
    }

    // Check for action buttons
    const buttons = await page.$$('button');
    log(`Found ${buttons.length} buttons on PM page`);

    // Look for Create/Add buttons
    const createButton = await page.$('button:has-text("Create"), button:has-text("Add"), button:has-text("New")');
    if (createButton) {
      results.passed.push('PM Module: Create button exists');
      log('PM Create button found', 'PASS');

      // Try clicking create button
      await createButton.click();
      await page.waitForTimeout(1000);
      await takeScreenshot(page, '11-pm-create-dialog');

      // Close dialog if opened
      const closeButton = await page.$('button:has-text("Cancel"), button:has-text("Close"), [aria-label="close"]');
      if (closeButton) {
        await closeButton.click();
        await page.waitForTimeout(500);
      }
    }

    // Check for tabs
    const tabs = await page.$$('[role="tab"], .MuiTab-root, .tab');
    if (tabs.length > 0) {
      log(`Found ${tabs.length} tabs on PM page`);
      for (let i = 0; i < Math.min(tabs.length, 3); i++) {
        try {
          await tabs[i].click();
          await page.waitForTimeout(1000);
          await takeScreenshot(page, `12-pm-tab-${i + 1}`);
          results.passed.push(`PM Module: Tab ${i + 1} works`);
        } catch (e) {
          log(`Tab ${i + 1} click failed`, 'WARN');
        }
      }
    }

  } catch (error) {
    results.failed.push(`PM Module: ${error.message}`);
    log(`PM Module error: ${error.message}`, 'FAIL');
  }
}

async function testMMModule(page) {
  log('=== Testing MM (Materials Management) Module ===');

  try {
    await page.goto(`${BASE_URL}/mm`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    await takeScreenshot(page, '20-mm-page');

    // Check for materials list
    const content = await page.textContent('body');
    if (content.includes('Material') || content.includes('material') || content.includes('MAT-')) {
      results.passed.push('MM Module: Materials data displayed');
      log('MM materials data found', 'PASS');
    }

    // Check for action buttons
    const createButton = await page.$('button:has-text("Create"), button:has-text("Add"), button:has-text("New")');
    if (createButton) {
      results.passed.push('MM Module: Create button exists');
      log('MM Create button found', 'PASS');

      await createButton.click();
      await page.waitForTimeout(1000);
      await takeScreenshot(page, '21-mm-create-dialog');

      const closeButton = await page.$('button:has-text("Cancel"), button:has-text("Close"), [aria-label="close"]');
      if (closeButton) {
        await closeButton.click();
        await page.waitForTimeout(500);
      }
    }

    // Check for tabs
    const tabs = await page.$$('[role="tab"], .MuiTab-root');
    if (tabs.length > 0) {
      log(`Found ${tabs.length} tabs on MM page`);
      for (let i = 0; i < Math.min(tabs.length, 3); i++) {
        try {
          await tabs[i].click();
          await page.waitForTimeout(1000);
          await takeScreenshot(page, `22-mm-tab-${i + 1}`);
        } catch (e) {}
      }
    }

  } catch (error) {
    results.failed.push(`MM Module: ${error.message}`);
    log(`MM Module error: ${error.message}`, 'FAIL');
  }
}

async function testFIModule(page) {
  log('=== Testing FI (Finance) Module ===');

  try {
    await page.goto(`${BASE_URL}/fi`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    await takeScreenshot(page, '30-fi-page');

    // Check for finance data
    const content = await page.textContent('body');
    if (content.includes('Cost') || content.includes('Approval') || content.includes('Budget') || content.includes('CC-')) {
      results.passed.push('FI Module: Finance data displayed');
      log('FI finance data found', 'PASS');
    }

    // Check for approval buttons
    const approveButton = await page.$('button:has-text("Approve")');
    const rejectButton = await page.$('button:has-text("Reject")');

    if (approveButton) {
      results.passed.push('FI Module: Approve button exists');
      log('FI Approve button found', 'PASS');
    }

    if (rejectButton) {
      results.passed.push('FI Module: Reject button exists');
      log('FI Reject button found', 'PASS');
    }

    // Check for tabs
    const tabs = await page.$$('[role="tab"], .MuiTab-root');
    if (tabs.length > 0) {
      log(`Found ${tabs.length} tabs on FI page`);
      for (let i = 0; i < Math.min(tabs.length, 3); i++) {
        try {
          await tabs[i].click();
          await page.waitForTimeout(1000);
          await takeScreenshot(page, `31-fi-tab-${i + 1}`);
        } catch (e) {}
      }
    }

  } catch (error) {
    results.failed.push(`FI Module: ${error.message}`);
    log(`FI Module error: ${error.message}`, 'FAIL');
  }
}

async function testTickets(page) {
  log('=== Testing Tickets ===');

  try {
    // Try different ticket URLs
    const ticketUrls = ['/tickets', '/all-tickets', '/pm'];
    let found = false;

    for (const url of ticketUrls) {
      await page.goto(`${BASE_URL}${url}`, { waitUntil: 'networkidle' });
      await page.waitForTimeout(1500);

      const content = await page.textContent('body');
      if (content.includes('TKT-') || content.includes('Ticket')) {
        found = true;
        await takeScreenshot(page, '40-tickets-page');
        results.passed.push('Tickets: Data displayed');
        log('Tickets data found', 'PASS');
        break;
      }
    }

    if (!found) {
      log('Tickets page not found or no ticket data', 'WARN');
    }

  } catch (error) {
    results.failed.push(`Tickets: ${error.message}`);
    log(`Tickets error: ${error.message}`, 'FAIL');
  }
}

async function testWorkOrderFlow(page) {
  log('=== Testing Work Order Flow ===');

  try {
    // Check if there's a work order flow section
    await page.goto(`${BASE_URL}/pm`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    const content = await page.textContent('body');
    if (content.includes('Work Order') || content.includes('WO-')) {
      results.passed.push('Work Order Flow: Data displayed');
      log('Work Order data found', 'PASS');
      await takeScreenshot(page, '50-work-orders');
    }

    // Look for work order specific buttons
    const checkMaterialsBtn = await page.$('button:has-text("Check Material"), button:has-text("Material Check")');
    const requestPurchaseBtn = await page.$('button:has-text("Request Purchase"), button:has-text("Purchase")');

    if (checkMaterialsBtn) {
      results.passed.push('Work Order Flow: Check Materials button exists');
      log('Check Materials button found', 'PASS');
    }

    if (requestPurchaseBtn) {
      results.passed.push('Work Order Flow: Request Purchase button exists');
      log('Request Purchase button found', 'PASS');
    }

  } catch (error) {
    results.failed.push(`Work Order Flow: ${error.message}`);
    log(`Work Order Flow error: ${error.message}`, 'FAIL');
  }
}

async function testAPIConnectivity(page) {
  log('=== Testing API Connectivity ===');

  try {
    // Check backend health
    const response = await page.request.get(`${API_URL}/health`);
    if (response.ok()) {
      results.passed.push('API: Backend health check');
      log('Backend API is healthy', 'PASS');
    }

    // Check if frontend can reach API (via browser network)
    await page.goto(`${BASE_URL}/pm`, { waitUntil: 'networkidle' });

    // Look for any error messages
    const content = await page.textContent('body');
    if (content.includes('Error') && content.includes('API')) {
      results.failed.push('API: Frontend-Backend connectivity issue');
      log('API connectivity issue detected', 'FAIL');
    } else {
      results.passed.push('API: Frontend-Backend connectivity');
      log('Frontend-Backend connectivity OK', 'PASS');
    }

  } catch (error) {
    results.failed.push(`API Connectivity: ${error.message}`);
    log(`API Connectivity error: ${error.message}`, 'FAIL');
  }
}

async function runTests() {
  console.log('\n' + '='.repeat(60));
  console.log('  SAP ERP Frontend - Automated Browser Testing');
  console.log('='.repeat(60) + '\n');

  // Create screenshots directory
  const fs = require('fs');
  if (!fs.existsSync('test-screenshots')) {
    fs.mkdirSync('test-screenshots');
  }

  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();

  try {
    // Test API first
    await testAPIConnectivity(page);

    // Test login
    const loggedIn = await testLogin(page);

    if (loggedIn) {
      // Test navigation
      await testNavigation(page);

      // Test each module
      await testPMModule(page);
      await testMMModule(page);
      await testFIModule(page);
      await testTickets(page);
      await testWorkOrderFlow(page);
    }

  } catch (error) {
    log(`Test execution error: ${error.message}`, 'FAIL');
  } finally {
    await browser.close();
  }

  // Print summary
  console.log('\n' + '='.repeat(60));
  console.log('  TEST RESULTS SUMMARY');
  console.log('='.repeat(60));
  console.log(`\n✅ PASSED: ${results.passed.length}`);
  results.passed.forEach(t => console.log(`   - ${t}`));

  console.log(`\n❌ FAILED: ${results.failed.length}`);
  results.failed.forEach(t => console.log(`   - ${t}`));

  console.log(`\n📸 Screenshots: ${results.screenshots.length}`);
  results.screenshots.forEach(s => console.log(`   - ${s}`));

  console.log('\n' + '='.repeat(60));
  const total = results.passed.length + results.failed.length;
  const passRate = total > 0 ? ((results.passed.length / total) * 100).toFixed(1) : 0;
  console.log(`  Pass Rate: ${passRate}% (${results.passed.length}/${total})`);
  console.log('='.repeat(60) + '\n');

  return results.failed.length === 0;
}

// Run tests
runTests()
  .then(success => process.exit(success ? 0 : 1))
  .catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
  });
