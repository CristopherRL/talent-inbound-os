/**
 * Next.js proxy for auth-based route protection (renamed from middleware in Next.js 16).
 *
 * In local development (same domain), the middleware can read the access_token
 * cookie and redirect unauthenticated users to /login.
 *
 * In production (cross-domain: frontend and backend on different subdomains),
 * the cookie is set on the backend domain and invisible to this middleware.
 * In that case, we skip the cookie check and let each page handle auth
 * via API calls — the backend validates the token on every request.
 */

import { NextRequest, NextResponse } from "next/server";

const AUTH_PATHS = ["/login", "/register"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasToken = request.cookies.has("access_token");

  // Redirect authenticated users away from auth pages (works in local dev)
  if (hasToken && AUTH_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/profile/:path*", "/ingest/:path*", "/chat/:path*", "/login", "/register"],
};
