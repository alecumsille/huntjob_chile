import { openai } from '@ai-sdk/openai';
import { google } from '@ai-sdk/google';
import { LanguageModel } from 'ai';

/**
 * Fallback AI execution strategy.
 * Tries the primary model (OpenAI GPT-4o) first.
 * If it fails (e.g. rate limit, API down), it catches the error
 * and retries with the secondary model (Google Gemini 1.5 Pro).
 */
export async function executeWithFallback<T>(
  action: (model: LanguageModel) => Promise<T>
): Promise<T> {
  const primaryModel = openai('gpt-4o');
  const secondaryModel = google('gemini-flash-latest');

  try {
    // Attempt with Primary Model
    return await action(primaryModel);
  } catch (error) {
    console.warn("Primary AI Model failed. Attempting fallback to Secondary Model.", error);
    try {
      // Attempt with Secondary Model
      return await action(secondaryModel);
    } catch (fallbackError) {
      console.error("Both AI Models failed.", fallbackError);
      throw new Error("El servicio de Inteligencia Artificial no está disponible temporalmente.");
    }
  }
}
