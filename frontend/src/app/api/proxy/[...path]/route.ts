/**
 * BizMind AI — Backend Proxy Route
 *
 * Proxies /api/proxy/[...path] → FastAPI backend (server-side).
 * This fixes the network-IP issue: the browser always calls the Next.js
 * server (same origin), which then forwards to localhost:8000 server-side.
 * Works correctly when accessed via any IP or hostname.
 */
import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

type Params = { path: string[] };

async function handler(
  request: NextRequest,
  { params }: { params: Promise<Params> }
) {
  const { path } = await params;
  const backendPath = "/" + path.join("/");

  // Preserve query string
  const search = request.nextUrl.search;
  const targetUrl = `${BACKEND_URL}${backendPath}${search}`;

  // Forward relevant headers (drop host)
  const forwardHeaders = new Headers();
  request.headers.forEach((value, key) => {
    if (!["host", "connection"].includes(key.toLowerCase())) {
      forwardHeaders.set(key, value);
    }
  });

  const body =
    request.method !== "GET" && request.method !== "HEAD"
      ? await request.arrayBuffer()
      : undefined;

  const backendRes = await fetch(targetUrl, {
    method: request.method,
    headers: forwardHeaders,
    body,
  });

  // Stream response back
  const resHeaders = new Headers();
  backendRes.headers.forEach((value, key) => {
    // Don't forward encoding headers that Next.js handles
    if (!["content-encoding", "transfer-encoding"].includes(key.toLowerCase())) {
      resHeaders.set(key, value);
    }
  });

  return new NextResponse(backendRes.body, {
    status: backendRes.status,
    headers: resHeaders,
  });
}

export const GET = handler;
export const POST = handler;
export const PUT = handler;
export const PATCH = handler;
export const DELETE = handler;
export const HEAD = handler;
export const OPTIONS = handler;
