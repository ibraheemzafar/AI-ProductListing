import { NextResponse, type NextRequest } from 'next/server';

const sessionCookieName = process.env.SESSION_COOKIE_NAME ?? 'apl_session';

export function middleware(request: NextRequest) {
  const hasSession = request.cookies.has(sessionCookieName);

  if (!hasSession) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('next', request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*'],
};
