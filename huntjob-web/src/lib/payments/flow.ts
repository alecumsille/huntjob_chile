import crypto from 'crypto';

interface FlowPaymentParams {
  commerceOrder: string;
  subject: string;
  currency?: string;
  amount: number;
  email: string;
  urlConfirmation: string;
  urlReturn: string;
  optional?: string;
}

export interface FlowPaymentResponse {
  url: string;
  token: string;
  flowOrder: number;
}

const FLOW_API_KEY = process.env.FLOW_API_KEY || '';
const FLOW_SECRET_KEY = process.env.FLOW_SECRET_KEY || '';
const FLOW_API_URL = process.env.FLOW_API_URL || 'https://www.flow.cl/api';

/**
 * Generates HMAC SHA256 signature for Flow.cl API
 * Concatenates sorted key + value and signs with FLOW_SECRET_KEY
 */
export function signFlowParams(params: Record<string, string | number>): string {
  const sortedKeys = Object.keys(params).sort();
  let toSign = '';
  for (const key of sortedKeys) {
    toSign += `${key}${params[key]}`;
  }
  return crypto.createHmac('sha256', FLOW_SECRET_KEY).update(toSign).digest('hex');
}

/**
 * Creates a payment order in Flow.cl and returns the redirect URL
 */
export async function createFlowPayment(data: FlowPaymentParams): Promise<FlowPaymentResponse> {
  if (!FLOW_API_KEY || !FLOW_SECRET_KEY) {
    throw new Error('Flow.cl API Key or Secret Key is missing in environment variables');
  }

  const params: Record<string, string | number> = {
    apiKey: FLOW_API_KEY,
    commerceOrder: data.commerceOrder,
    subject: data.subject,
    currency: data.currency || 'CLP',
    amount: data.amount,
    email: data.email,
    urlConfirmation: data.urlConfirmation,
    urlReturn: data.urlReturn,
  };

  if (data.optional) {
    params.optional = data.optional;
  }

  const s = signFlowParams(params);
  params.s = s;

  const formData = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    formData.append(key, String(value));
  }

  const response = await fetch(`${FLOW_API_URL}/payment/create`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData.toString(),
  });

  const result = await response.json();

  if (!response.ok || result.code) {
    console.error('[Flow API Error]', result);
    throw new Error(result.message || `Error al crear orden en Flow (código ${result.code})`);
  }

  return {
    url: `${result.url}?token=${result.token}`,
    token: result.token,
    flowOrder: result.flowOrder,
  };
}

/**
 * Gets payment status from Flow.cl using token
 */
export async function getFlowPaymentStatus(token: string) {
  const params: Record<string, string> = {
    apiKey: FLOW_API_KEY,
    token: token,
  };

  const s = signFlowParams(params);
  params.s = s;

  const query = new URLSearchParams(params).toString();
  const response = await fetch(`${FLOW_API_URL}/payment/getStatus?${query}`, {
    method: 'GET',
  });

  const result = await response.json();
  if (!response.ok || result.code) {
    console.error('[Flow getStatus Error]', result);
    throw new Error(result.message || 'Error al obtener estado de pago en Flow');
  }

  return result;
}
