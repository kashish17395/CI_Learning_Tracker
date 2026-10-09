const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require('../frontend/node_modules/playwright');

(async () => {
  const root = path.resolve(__dirname, '..');
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 900, height: 1250 }, deviceScaleFactor: 1 });
    await page.goto(pathToFileURL(path.join(root, 'docs', 'management-overview.html')).href);
    await page.emulateMedia({ media: 'print' });
    const layout = await page.locator('.sheet').evaluateAll(sheets => sheets.map((sheet, i) => {
      const footer = sheet.querySelector('footer').getBoundingClientRect();
      const paragraphs = sheet.querySelectorAll(':scope > p');
      const last = paragraphs[paragraphs.length - 1].getBoundingClientRect();
      return { page: i + 1, clearance: Math.round(footer.top - last.bottom) };
    }));
    if (layout.some(item => item.clearance < 8)) throw new Error('Content overlaps the footer: ' + JSON.stringify(layout));
    await page.pdf({ path: path.join(root, 'docs', 'management-overview.pdf'), printBackground: true, preferCSSPageSize: true });
    for (let n = 0; n < 2; n++) {
      await page.locator('.sheet').nth(n).screenshot({ path: path.join(root, 'docs', `management-overview-page-${n + 1}.png`) });
    }
    console.log('PDF exported. Page layout:', JSON.stringify(layout));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
