import { chromium, Page, Browser } from 'playwright';

/**
 * Enhanced Playwright Scraper with Anti-Bot Evasion & Stealth Headers.
 */
export class PlaywrightScraper {
  private browser: Browser | null = null;
  private page: Page | null = null;

  /**
   * Initializes the browser with evasion techniques (Anti-Bot & Stealth).
   */
  async init() {
    try {
      this.browser = await chromium.launch({
        headless: true,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-blink-features=AutomationControlled',
          '--disable-infobars',
          '--window-size=1920,1080',
          '--start-maximized',
        ],
      });
      const context = await this.browser.newContext({
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        viewport: { width: 1920, height: 1080 },
        extraHTTPHeaders: {
          'Accept-Language': 'es-CL,es;q=0.9,en-US;q=0.8,en;q=0.7',
          'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
          'Sec-Ch-Ua-Mobile': '?0',
          'Sec-Ch-Ua-Platform': '"Windows"',
          'Sec-Fetch-Dest': 'document',
          'Sec-Fetch-Mode': 'navigate',
          'Sec-Fetch-Site': 'none',
          'Sec-Fetch-User': '?1',
          'Upgrade-Insecure-Requests': '1',
        },
      });
      this.page = await context.newPage();

      // Stealth injection: remove navigator.webdriver flag
      await this.page.addInitScript(() => {
        Object.defineProperty(navigator, 'webdriver', {
          get: () => undefined,
        });
      });
    } catch (e) {
      console.warn('[PlaywrightScraper] Could not initialize Chromium instance, fallback HTTP fetch will be used if needed:', e);
    }
  }

  /**
   * Navigates to a URL and returns the raw HTML content.
   * Includes fallback to HTTP fetch if headless browser is unavailable in serverless environment.
   */
  async getRawHtml(url: string, waitForSelector?: string): Promise<string> {
    if (this.page) {
      try {
        await this.page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
        
        if (waitForSelector) {
          await this.page.waitForSelector(waitForSelector, { timeout: 8000 }).catch(() => {
            console.warn(`Timeout waiting for selector: ${waitForSelector}`);
          });
        }

        // Scroll to bottom to trigger lazy loading if any
        await this.page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
        await this.page.waitForTimeout(1000);

        return await this.page.content();
      } catch (err) {
        console.warn('[PlaywrightScraper] Page navigation failed, using fallback HTTP fetcher:', err);
      }
    }

    // Fallback: Direct HTTP fetch with desktop User-Agent
    console.log('[PlaywrightScraper] Executing fallback HTTP fetch for:', url);
    const res = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-CL,es;q=0.9,en;q=0.8',
      },
    });

    if (!res.ok) {
      throw new Error(`Error al obtener contenido de la oferta (${res.status} ${res.statusText})`);
    }

    return await res.text();
  }

  /**
   * Closes the browser instance.
   */
  async close() {
    if (this.browser) {
      await this.browser.close().catch(() => {});
      this.browser = null;
      this.page = null;
    }
  }
}
