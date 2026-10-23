// Run the unchanged legacy suite in its original professional table presentation.
const { chromium } = require('playwright');
const launch = chromium.launch.bind(chromium);
chromium.launch = async (...args) => {
  const browser = await launch(...args);
  const newPage = browser.newPage.bind(browser);
  browser.newPage = async (...pageArgs) => {
    const page = await newPage(...pageArgs);
    await page.addInitScript(() => { try { localStorage.setItem('tradepulse.view', 'pro'); } catch {} });
    return page;
  };
  return browser;
};
