/**
 * Next.js proxy for auth-based route protection (renamed from middleware in Next.js 16).
 *
 * This runs on the Node.js runtime BEFORE a page is rendered.
 * It checks for the access_token cookie:
 * - If the user is NOT authenticated and tries to access a protected page → redirect to /login
 * - If the user IS authenticated and tries to access /login or /register → redirect to /dashboard
 *
 * Note: This only checks cookie EXISTENCE, not validity. The backend validates
 * the actual token on every API call. This is a UX optimization to avoid
 * showing protected pages to users whose cookie has been cleared.
 */

import { NextRequest, NextResponse } from "next/server";

const PROTECTED_PATHS = ["/dashboard", "/profile", "/ingest", "/chat"];
const AUTH_PATHS = ["/login", "/register"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasToken = request.cookies.has("access_token");

  // Redirect unauthenticated users away from protected pages
  if (!hasToken && PROTECTED_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  // Redirect authenticated users away from auth pages
  if (hasToken && AUTH_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/profile/:path*", "/ingest/:path*", "/chat/:path*", "/login", "/register"],
};
