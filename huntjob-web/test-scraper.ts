import { scrapeJobOffer } from './src/lib/scraper/extractor';
import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

async function runTest() {
  console.log('🤖 Iniciando prueba del Scraper Híbrido (Playwright + AI)...');
  const testUrl = 'https://www.getonbrd.com/jobs/programming/full-stack-developer-ruby-on-rails-faktiva-remote';
  
  try {
    console.log(`🌐 Navegando a: ${testUrl}`);
    const jobOffer = await scrapeJobOffer(testUrl, 'GetOnBoard');
    
    console.log('✅ ¡Vacante extraída y estructurada con éxito!');
    console.log(JSON.stringify(jobOffer, null, 2));
  } catch (error) {
    console.error('❌ Error durante el scraping:', error);
  }
}

runTest();
