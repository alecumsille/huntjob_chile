import { chromium, Page, Browser } from 'playwright';

/**
 * Interface for the Playwright scraper module.
 */
export class PlaywrightScraper {
  private browser: Browser | null = null;
  private page: Page | null = null;

  /**
   * Initializes the browser with evasion techniques (Anti-Bot).
   */
  async init() {
    this.browser = await chromium.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-blink-features=AutomationControlled',
      ],
    });
    const context = await this.browser.newContext({
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      viewport: { width: 1920, height: 1080 },
    });
    this.page = await context.newPage();
  }

  /**
   * Navigates to a URL and returns the raw HTML content.
   */
  async getRawHtml(url: string, waitForSelector?: string): Promise<string> {
    if (!this.page) throw new Error("Scraper not initialized. Call init() first.");

    await this.page.goto(url, { waitUntil: 'domcontentloaded' });
    
    if (waitForSelector) {
      await this.page.waitForSelector(waitForSelector, { timeout: 10000 }).catch(() => {
        console.warn(`Timeout waiting for selector: ${waitForSelector}`);
      });
    }

    // Scroll to bottom to trigger lazy loading if any
    await this.page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await this.page.waitForTimeout(2000); // Artificial delay to mimic human behavior

    return await this.page.content();
  }

  /**
   * Closes the browser instance.
   */
  async close() {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
      this.page = null;
    }
  }
}
