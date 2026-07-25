/**
 * Security Sanitizer — protección contra prompt injection y abuso.
 *
 * Centraliza la lógica de sanitización para que todas las rutas API la reutilicen.
 */

// Patrones comunes de prompt injection
const INJECTION_PATTERNS: RegExp[] = [
  /ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)/i,
  /disregard\s+(all\s+)?(previous|prior|above)/i,
  /forget\s+(everything|all|your)\s+(instructions?|rules?|training)/i,
  /you\s+are\s+now\s+(a|an|the)\s+/i,
  /new\s+instructions?:\s*/i,
  /system\s*prompt\s*:/i,
  /\[SYSTEM\]/i,
  /\<\|im_start\|\>/i,
  /\<\|im_end\|\>/i,
  /\<\|endoftext\|\>/i,
  /\<\/?system\>/i,
  /act\s+as\s+(if|though)?\s*(you\s+are|a|an)/i,
  /pretend\s+(you\s+are|to\s+be)/i,
  /override\s+(your|all|the)\s+(instructions?|rules?|guidelines?)/i,
  /reveal\s+(your|the)\s+(system|initial|original)\s*(prompt|instructions?)/i,
  /what\s+(are|is)\s+your\s+(system|initial|original)\s*(prompt|instructions?)/i,
  /repeat\s+(your|the)\s+(system|initial)\s*(prompt|instructions?)/i,
  /jailbreak/i,
  /DAN\s*mode/i,
  /developer\s*mode/i,
];

export interface SanitizeResult {
  safe: boolean;
  reason?: string;
  cleanedText?: string;
}

/**
 * Detecta intentos de prompt injection en un texto.
 */
export function detectPromptInjection(text: string): SanitizeResult {
  for (const pattern of INJECTION_PATTERNS) {
    if (pattern.test(text)) {
      return {
        safe: false,
        reason: `Se detectó un patrón potencialmente malicioso en tu mensaje.`,
      };
    }
  }
  return { safe: true, cleanedText: text };
}

/**
 * Limpia un texto eliminando caracteres de control invisibles y normalizando
 * caracteres Unicode sospechosos que se usan para evadir filtros.
 */
export function sanitizeText(text: string): string {
  return text
    // Eliminar caracteres de control (excepto newline y tab)
    .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '')
    // Normalizar whitespace excesivo
    .replace(/\n{4,}/g, '\n\n\n')
    // Eliminar zero-width characters usados para evadir filtros
    .replace(/[\u200B\u200C\u200D\uFEFF\u00AD]/g, '')
    .trim();
}

/**
 * Valida el tamaño del payload de un request antes de procesarlo.
 */
export function validatePayloadSize(
  payload: unknown,
  maxBytes: number = 100_000
): SanitizeResult {
  const size = new TextEncoder().encode(JSON.stringify(payload)).length;
  if (size > maxBytes) {
    return {
      safe: false,
      reason: `El payload excede el límite de ${Math.round(maxBytes / 1000)}KB.`,
    };
  }
  return { safe: true };
}

/**
 * Pipeline completo de sanitización para mensajes de chat.
 * Retorna el texto limpio o un error.
 */
export function sanitizeChatMessage(content: string): SanitizeResult {
  // 1. Limpiar caracteres invisibles
  const cleaned = sanitizeText(content);

  // 2. Verificar longitud post-limpieza
  if (cleaned.length === 0) {
    return { safe: false, reason: 'El mensaje está vacío.' };
  }

  if (cleaned.length > 4000) {
    return { safe: false, reason: 'El mensaje excede el límite de 4000 caracteres.' };
  }

  // 3. Detectar prompt injection
  const injectionCheck = detectPromptInjection(cleaned);
  if (!injectionCheck.safe) {
    return injectionCheck;
  }

  return { safe: true, cleanedText: cleaned };
}

/**
 * Sanitiza las respuestas generadas por la IA para prevenir XSS o inyección de scripts.
 */
export function sanitizeAiOutput(output: string): string {
  if (!output) return '';
  return output
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '')
    .replace(/javascript:/gi, '')
    .replace(/onerror=/gi, '')
    .replace(/onload=/gi, '');
}

