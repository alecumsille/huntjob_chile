import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'
import { Ratelimit } from '@upstash/ratelimit'
import { Redis } from '@upstash/redis'

// Rate limiters diferenciados por tipo de ruta
const redis = (process.env.UPSTASH_REDIS_REST_URL && process.env.UPSTASH_REDIS_REST_TOKEN)
  ? Redis.fromEnv()
  : null;

// API general: 10 req/min
const apiRatelimit = redis
  ? new Ratelimit({ redis, limiter: Ratelimit.slidingWindow(10, '1 m'), prefix: 'rl:api', analytics: true })
  : null;

// Rutas de IA (chat, apply): 5 req/min — más costosas
const aiRatelimit = redis
  ? new Ratelimit({ redis, limiter: Ratelimit.slidingWindow(5, '1 m'), prefix: 'rl:ai', analytics: true })
  : null;

// Auth attempts: 3 req/min — prevenir brute-force
const authRatelimit = redis
  ? new Ratelimit({ redis, limiter: Ratelimit.slidingWindow(3, '1 m'), prefix: 'rl:auth', analytics: true })
  : null;

function getClientIdentifier(request: NextRequest, userId?: string): string {
  return userId || request.headers.get('x-real-ip') || request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || '127.0.0.1';
}

function isAiRoute(pathname: string): boolean {
  return pathname.startsWith('/api/chat') || pathname.startsWith('/api/apply') || pathname.startsWith('/api/cv/parse');
}

function isAuthRoute(pathname: string): boolean {
  return pathname.startsWith('/auth/');
}

export async function middleware(request: NextRequest) {
  let supabaseResponse = NextResponse.next({
    request,
  })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://dummy.supabase.co',
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'dummy_key',
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
          supabaseResponse = NextResponse.next({
            request,
          })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  const {
    data: { user },
  } = await supabase.auth.getUser()

  const pathname = request.nextUrl.pathname;
  const identifier = getClientIdentifier(request, user?.id);

  // Rate limiting diferenciado
  if (pathname.startsWith('/api/') || isAuthRoute(pathname)) {
    let limiter: Ratelimit | null = null;
    
    if (isAiRoute(pathname)) {
      limiter = aiRatelimit;
    } else if (isAuthRoute(pathname)) {
      limiter = authRatelimit;
    } else if (pathname.startsWith('/api/')) {
      limiter = apiRatelimit;
    }

    if (limiter) {
      const { success, limit, reset, remaining } = await limiter.limit(identifier);
      
      if (!success) {
        console.log(`[AUDIT] ${JSON.stringify({
          timestamp: new Date().toISOString(),
          action: 'ratelimit.exceeded',
          userId: user?.id,
          ip: request.headers.get('x-forwarded-for'),
          path: pathname,
        })}`);
        
        return NextResponse.json(
          { error: 'Demasiadas solicitudes. Intenta de nuevo en un momento.' },
          { 
            status: 429, 
            headers: {
              'X-RateLimit-Limit': limit.toString(),
              'X-RateLimit-Remaining': remaining.toString(),
              'X-RateLimit-Reset': reset.toString(),
              'Retry-After': Math.ceil((reset - Date.now()) / 1000).toString(),
            }
          }
        );
      }
    }
  }

  // Bloquear APIs para usuarios no autenticados
  if (pathname.startsWith('/api/') && !user) {
    console.log(`[AUDIT] ${JSON.stringify({
      timestamp: new Date().toISOString(),
      action: 'auth.unauthorized',
      ip: request.headers.get('x-forwarded-for'),
      path: pathname,
    })}`);
    return NextResponse.json({ error: 'No autorizado' }, { status: 401 });
  }

  // Protect /dashboard route
  if (pathname.startsWith('/dashboard') && !user) {
    const url = request.nextUrl.clone()
    url.pathname = '/auth/login'
    return NextResponse.redirect(url)
  }

  // Redirect away from login if already authenticated
  if (pathname === '/auth/login' && user) {
    const url = request.nextUrl.clone()
    url.pathname = '/dashboard'
    return NextResponse.redirect(url)
  }

  // Agregar headers de seguridad
  supabaseResponse.headers.set('X-Content-Type-Options', 'nosniff');
  supabaseResponse.headers.set('X-Frame-Options', 'DENY');
  supabaseResponse.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');

  return supabaseResponse
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
