const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');

(async () => {
  const root = path.resolve(__dirname, '..');
  const browser = await chromium.launch({headless: true, channel: 'msedge'});
  const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
  const counts = {};
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  try {
    for (let i = 1; i <= 11; i++) {
      const cid = `ch${String(i).padStart(2, '0')}`;
      const source = JSON.parse(fs.readFileSync(path.join(root, 'source', cid + '.json'), 'utf8'));
      const translations = JSON.parse(fs.readFileSync(path.join(root, 'translations', cid + '.json'), 'utf8'));
      const sections = source.blocks.filter(b => /^\d+(?:\.\d+)+\s/.test(b.en));
      const expected = sections.map(b => ({href: '#' + b.id, label: translations[b.id].split('\n')[0]}));
      await page.goto(pathToFileURL(path.join(root, 'output/reader', cid + '.html')).href);
      for (const selector of ['.local-toc', '.sidebar-sections']) {
        const actual = await page.locator(selector + ' a').evaluateAll(links => links.map(a => ({href: a.getAttribute('href'), label: a.textContent})));
        assert.deepEqual(actual, expected, cid + ': ' + selector);
        const nested = await page.locator(selector + ' .section-links .section-links a').count();
        assert.equal(nested, sections.filter(b => /^\d+\.\d+\.\d+\s/.test(b.en)).length);
      }
      assert.equal(await page.locator('.local-toc').getAttribute('open'), '');
      counts[cid] = sections.length;
    }
    await page.goto(pathToFileURL(path.join(root, 'output/reader/ch08.html')).href);
    await page.screenshot({path: path.join(root, 'qa/desktop-section-index.png')});
    await page.evaluate(() => document.documentElement.style.scrollBehavior = 'auto');
    await page.locator('.local-toc a[href="#p198b04"]').click();
    assert.equal(new URL(page.url()).hash, '#p198b04');
    assert(await page.locator('#p198b04').evaluate(el => el.getBoundingClientRect().top >= document.querySelector('.topbar').getBoundingClientRect().bottom));
    await page.setViewportSize({width: 390, height: 844});
    await page.locator('#navtoggle').click();
    await page.locator('.sidebar-sections a[href="#p175b05"]').scrollIntoViewIfNeeded();
    await page.screenshot({path: path.join(root, 'qa/mobile-section-index.png')});
    await page.locator('.sidebar-sections a[href="#p175b05"]').click();
    assert.equal(new URL(page.url()).hash, '#p175b05');
    assert.equal(await page.locator('.sidebar').isVisible(), false);
    assert.equal(await page.locator('#navtoggle').getAttribute('aria-expanded'), 'false');
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    assert.deepEqual(errors, []);
    const report = {chapters: counts, totalSections: Object.values(counts).reduce((a, b) => a + b, 0), desktopJump: true, mobileJump: true, passed: true};
    fs.writeFileSync(path.join(root, 'qa/section-index-checks.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report, null, 2));
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error); process.exitCode = 1;});
