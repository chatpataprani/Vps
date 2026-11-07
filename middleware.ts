import { NextRequest, NextResponse } from "next/server";

/** HTTP Basic gate. Fail closed when credentials are missing. */
export function middleware(req: NextRequest) {
  const user = process.env.PANEL_USERNAME;
  const pass = process.env.PANEL_PASSWORD;
  if (!user || !pass) {
    return new NextResponse("Panel authentication is not configured. Set PANEL_USERNAME and PANEL_PASSWORD.", {
      status: 503, headers: { "Cache-Control": "no-store" },
    });
  }
  const auth = req.headers.get("authorization") || "";
  if (auth.startsWith("Basic ")) {
    try {
      const [providedUser, ...rest] = atob(auth.slice(6)).split(":");
      const providedPass = rest.join(":");
      if (providedUser === user && providedPass === pass) return NextResponse.next();
    } catch {}
  }
  return new NextResponse("Authentication required", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="Vps Control Panel", charset="UTF-8"', "Cache-Control": "no-store" },
  });
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)"],
};