import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { createServerClient } from '@supabase/ssr';
import { createFlowPayment } from '@/lib/payments/flow';
import { auditLog } from '@/lib/security/audit-log';

const PLAN_PRICES: Record<string, { amount: number; name: string }> = {
  pro: { amount: 9900, name: 'HuntJob Pro (Mensual)' },
  enterprise: { amount: 29900, name: 'HuntJob Enterprise' },
};

export async function POST(req: Request) {
  try {
    const cookieStore = await cookies();
    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://dummy.supabase.co',
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'dummy_key',
      {
        cookies: {
          getAll() {
            return cookieStore.getAll();
          },
        },
      }
    );

    const { data: { user } } = await supabase.auth.getUser();

    if (!user) {
      auditLog({ action: 'auth.unauthorized', path: '/api/payments/create', ip: req.headers.get('x-forwarded-for') ?? undefined });
      return NextResponse.json({ error: 'Debes iniciar sesión para suscribirte.' }, { status: 401 });
    }

    const json = await req.json().catch(() => ({}));
    const planKey = json.plan || 'pro';
    const planInfo = PLAN_PRICES[planKey];

    if (!planInfo) {
      return NextResponse.json({ error: 'Plan no válido' }, { status: 400 });
    }

    const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'https://huntjob.cumsille.me';
    const commerceOrder = `HJ-${user.id.slice(0, 8)}-${Date.now()}`;

    const flowPayment = await createFlowPayment({
      commerceOrder,
      subject: `Suscripción ${planInfo.name}`,
      amount: planInfo.amount,
      email: user.email || 'usuario@huntjob.cl',
      urlConfirmation: `${baseUrl}/api/payments/confirm`,
      urlReturn: `${baseUrl}/dashboard/settings?payment=return`,
      optional: JSON.stringify({ userId: user.id, plan: planKey }),
    });

    auditLog({
      action: 'chat.request', // reuse action logger
      userId: user.id,
      path: '/api/payments/create',
      details: { plan: planKey, commerceOrder, amount: planInfo.amount },
    });

    return NextResponse.json({
      success: true,
      url: flowPayment.url,
      token: flowPayment.token,
      commerceOrder,
    });

  } catch (error) {
    console.error('[Payment Create Error]', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Error al iniciar proceso de pago' },
      { status: 500 }
    );
  }
}
