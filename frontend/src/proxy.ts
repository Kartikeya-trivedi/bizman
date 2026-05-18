/**
 * BizMind AI — Next.js 16 Proxy (Route Protection)
 * Replaces the deprecated "middleware" convention in Next.js 16.
 * Redirects unauthenticated users to /login for all dashboard routes.
 * Token presence is checked via cookie (set client-side after login).
 * Full JWT verification is handled by the FastAPI backend on each request.
 */
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_ROUTES = ["/login", "/api"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Always allow public routes and Next.js internals
  if (PUBLIC_ROUTES.some((route) => pathname.startsWith(route))) {
    return NextResponse.next();
  }

  // Check for JWT cookie written by auth.ts setSession()
  const token = request.cookies.get("bizmind_token")?.value;

  if (!token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
