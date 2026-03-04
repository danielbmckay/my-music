#!/usr/bin/env node
/**
 * Download all pages from Canva designs.
 *
 * Strategy: Open the design, switch to Pages panel, scroll to load ALL pages,
 * then navigate to each page and screenshot the canvas area.
 *
 * Usage: node Tools/canva_download.js
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const DESIGNS = [
  {
    name: '89 Vision',
    url: 'https://www.canva.com/design/DAGEUApoM_o/BpYfT5wGSMTZn86ofuN0Zw/edit',
    expectedPages: 111
  },
  {
    name: 'AA Audible',
    url: 'https://www.canva.com/design/DAGL66ErbeI/T_vv9LsNrWMCZ9-KR4xnzA/edit',
    expectedPages: 37
  }
];

const OUTPUT_DIR = path.join(__dirname, '..', 'Claude', 'claude-temp', 'canva-artwork');
const USER_DATA_DIR = path.join(__dirname, '..', '.playwright-profile');

async function scrollAndCollectPages(page, expectedCount) {
  // Click Pages button in the footer to open the page thumbnails panel
  const pagesBtn = page.locator('button:has-text("Pages")').first();
  await pagesBtn.click();
  await page.waitForTimeout(2000);

  // Now we need to scroll the pages panel to load all thumbnails
  // The pages panel has page title inputs we can count
  let titles = [];
  let lastCount = 0;
  let stableRounds = 0;

  for (let attempt = 0; attempt < 50; attempt++) {
    // Scroll the pages panel container down
    await page.evaluate(() => {
      // Find the scrollable container that holds page thumbnails
      const containers = document.querySelectorAll('[class*="scroll"], [style*="overflow"]');
      for (const c of containers) {
        if (c.querySelector('input[aria-label="Page title"]')) {
          c.scrollTop = c.scrollHeight;
          return true;
        }
      }
      // Fallback: find page inputs and scroll the last one into view
      const inputs = document.querySelectorAll('input[aria-label="Page title"]');
      if (inputs.length > 0) {
        inputs[inputs.length - 1].scrollIntoView({ behavior: 'instant' });
        return true;
      }
      return false;
    });
    await page.waitForTimeout(800);

    const currentCount = await page.evaluate(() =>
      document.querySelectorAll('input[aria-label="Page title"]').length
    );

    if (currentCount === lastCount) {
      stableRounds++;
      if (stableRounds >= 5 || currentCount >= expectedCount) break;
    } else {
      stableRounds = 0;
      lastCount = currentCount;
      console.log(`    Loaded ${currentCount} pages so far...`);
    }
  }

  // Collect all titles
  titles = await page.evaluate(() => {
    const results = [];
    document.querySelectorAll('input[aria-label="Page title"]').forEach((input, i) => {
      results.push({ page: i + 1, title: input.value || `Page ${i + 1}` });
    });
    return results;
  });

  return titles;
}

async function navigateToPage(page, pageNum) {
  // Click on the page thumbnail to navigate to it
  // The page number display in the footer shows "X / Y"
  // We can click the page counter and type the page number
  const pageCounter = page.locator('button:has-text("/ ")').first();
  if (await pageCounter.isVisible().catch(() => false)) {
    await pageCounter.click();
    await page.waitForTimeout(300);
    // Type the page number in the input that appears
    const pageInput = page.locator('input[type="text"]').last();
    if (await pageInput.isVisible().catch(() => false)) {
      await pageInput.fill(String(pageNum));
      await pageInput.press('Enter');
      await page.waitForTimeout(1000);
      return;
    }
  }

  // Fallback: use keyboard navigation (Ctrl+Shift+G or Page Down)
  // First go to page 1
  await page.keyboard.press('Home');
  await page.waitForTimeout(200);
  for (let i = 1; i < pageNum; i++) {
    await page.keyboard.press('PageDown');
    await page.waitForTimeout(100);
  }
  await page.waitForTimeout(500);
}

async function screenshotCurrentPage(page, outputPath) {
  // Find the canvas/design area and screenshot it
  // The design area is inside main[aria-label="Canvas"]
  const canvas = page.locator('main[aria-label="Canvas"]').first();
  if (await canvas.isVisible().catch(() => false)) {
    await canvas.screenshot({ path: outputPath });
    return true;
  }

  // Fallback: screenshot the center of the viewport (the design)
  const clip = await page.evaluate(() => {
    const main = document.querySelector('main') || document.querySelector('[class*="canvas"]');
    if (main) {
      const rect = main.getBoundingClientRect();
      return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
    }
    // Default: center area
    return { x: 200, y: 50, width: 1000, height: 800 };
  });
  await page.screenshot({ path: outputPath, clip });
  return true;
}

async function main() {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  console.log('Launching browser...');
  console.log('If you need to log into Canva, do so in the browser window, then press Enter.\n');

  const browser = await chromium.launchPersistentContext(USER_DATA_DIR, {
    headless: false,
    viewport: { width: 1400, height: 900 },
    args: ['--disable-blink-features=AutomationControlled']
  });

  const page = browser.pages()[0] || await browser.newPage();

  for (const design of DESIGNS) {
    console.log(`\n=== ${design.name} (expecting ${design.expectedPages} pages) ===`);
    const designDir = path.join(OUTPUT_DIR, design.name.replace(/'/g, ''));
    fs.mkdirSync(designDir, { recursive: true });

    console.log('  Opening design...');
    await page.goto(design.url, { waitUntil: 'networkidle', timeout: 60000 });
    await page.waitForTimeout(3000);

    // Check if login needed
    const url = page.url();
    if (url.includes('login') || url.includes('signin') || !url.includes('canva.com/design')) {
      console.log('\n>>> Please log into Canva, then press Enter <<<');
      await new Promise(resolve => process.stdin.once('data', resolve));
      await page.goto(design.url, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(3000);
    }

    // Handle "Continue in browser"
    try {
      const btn = page.getByText('Continue in browser');
      if (await btn.isVisible({ timeout: 3000 })) {
        await btn.click();
        await page.waitForTimeout(2000);
      }
    } catch (e) {}

    // Dismiss any popups/tooltips
    await page.keyboard.press('Escape');
    await page.waitForTimeout(500);

    // Get ALL page titles by scrolling through the pages panel
    console.log('  Loading all pages (scrolling)...');
    const titles = await scrollAndCollectPages(page, design.expectedPages);
    console.log(`  Found ${titles.length} pages total`);

    // Save page map
    const mapPath = path.join(designDir, 'page-map.json');
    fs.writeFileSync(mapPath, JSON.stringify(titles, null, 2));

    // Close the pages panel
    await page.keyboard.press('Escape');
    await page.waitForTimeout(500);

    // Screenshot each page
    let downloaded = 0;
    for (const { page: pageNum, title } of titles) {
      const safeName = title.replace(/[^a-zA-Z0-9 _()'-]/g, '').trim();
      const filename = `${String(pageNum).padStart(3, '0')}-${safeName}.png`;
      const outputPath = path.join(designDir, filename);

      if (fs.existsSync(outputPath)) {
        downloaded++;
        continue; // Skip already downloaded
      }

      try {
        await navigateToPage(page, pageNum);
        await screenshotCurrentPage(page, outputPath);
        downloaded++;
        if (downloaded % 10 === 0 || downloaded === titles.length) {
          console.log(`  Progress: ${downloaded}/${titles.length}`);
        }
      } catch (err) {
        console.error(`  Error page ${pageNum} (${title}): ${err.message}`);
      }
    }

    console.log(`  Done: ${downloaded} pages saved to ${designDir}/`);
  }

  console.log('\n=== Complete! ===');
  await browser.close();
}

main().catch(err => {
  console.error('Fatal:', err);
  process.exit(1);
});
