/**
 * Audit Logger — registro centralizado de uso de APIs sensibles.
 *
 * Escribe logs estructurados a stdout (capturados por Vercel Logs) para
 * monitoreo, detección de abuso y auditoría.
 */

export type AuditAction =
  | 'chat.request'
  | 'chat.blocked'
  | 'apply.request'
  | 'apply.blocked'
  | 'evaluate.request'
  | 'evaluate.blocked'
  | 'export.request'
  | 'export.blocked'
  | 'ratelimit.exceeded'
  | 'injection.detected'
  | 'auth.unauthorized';

export interface AuditEntry {
  timestamp: string;
  action: AuditAction;
  userId?: string;
  ip?: string;
  path: string;
  details?: Record<string, unknown>;
}

/**
 * Registra un evento de auditoría como JSON estructurado en stdout.
 * Vercel Logs captura automáticamente estos registros.
 */
export function auditLog(entry: Omit<AuditEntry, 'timestamp'>): void {
  const log: AuditEntry = {
    timestamp: new Date().toISOString(),
    ...entry,
  };
  // JSON estructurado para fácil parseo en Vercel Logs / Datadog / etc.
  console.log(`[AUDIT] ${JSON.stringify(log)}`);
}
