import { NextResponse } from 'next/server';
import { getFlowPaymentStatus } from '@/lib/payments/flow';
import { createClient } from '@supabase/supabase-js';
import { auditLog } from '@/lib/security/audit-log';

export async function POST(req: Request) {
  try {
    const formData = await req.formData();
    const token = formData.get('token') as string;

    if (!token) {
      return NextResponse.json({ error: 'Token no recibido' }, { status: 400 });
    }

    const statusData = await getFlowPaymentStatus(token);
    console.log('[Flow Webhook Confirmation]', statusData);

    // Flow status: 2 = Pagado, 3 = Rechazado, 4 = Anulado
    if (statusData.status === 2) {
      let optionalData: { userId?: string; plan?: string } = {};
      try {
        if (statusData.optional) {
          optionalData = JSON.parse(statusData.optional);
        }
      } catch (e) {
        console.warn('Failed to parse optional payload from Flow', e);
      }

      const userId = optionalData.userId;
      const plan = optionalData.plan || 'pro';

      if (userId && process.env.SUPABASE_SERVICE_ROLE_KEY) {
        const supabase = createClient(
          process.env.NEXT_PUBLIC_SUPABASE_URL!,
          process.env.SUPABASE_SERVICE_ROLE_KEY
        );

        // Actualizar plan en tabla profiles
        const { error: profileError } = await supabase
          .from('profiles')
          .update({ 
            plan: plan, 
            ai_credits_limit: plan === 'pro' ? 100 : 500,
            updated_at: new Date().toISOString() 
          })
          .eq('id', userId);

        if (profileError) {
          console.error('[Flow Webhook] Error updating profile:', profileError);
        }

        // Registrar pago en tabla payments
        await supabase.from('payments').insert({
          user_id: userId,
          flow_order_id: String(statusData.flowOrder),
          flow_payment_status: 'PAID',
          amount: statusData.amount,
          currency: statusData.currency || 'CLP',
          plan: plan,
        });

        auditLog({
          action: 'apply.request',
          userId: userId,
          path: '/api/payments/confirm',
          details: { flowOrder: statusData.flowOrder, plan, amount: statusData.amount },
        });
      }
    }

    return NextResponse.json({ status: 'OK' });
  } catch (error) {
    console.error('[Flow Webhook Error]', error);
    return NextResponse.json({ error: 'Error procesando webhook de Flow' }, { status: 500 });
  }
}
