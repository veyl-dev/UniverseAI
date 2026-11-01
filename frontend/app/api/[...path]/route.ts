import { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type RouteContext = { params: { path: string[] } };

function backendBase(): string {
  const configured = process.env.API_INTERNAL_URL || "http://127.0.0.1:8000";
  const withProtocol = /^https?:\/\//i.test(configured) ? configured : "https://" + configured;
  return withProtocol.replace(/\/$/, "");
}

async function proxy(request: NextRequest, context: RouteContext): Promise<Response> {
  const path = (context.params.path || []).map((part) => encodeURIComponent(part)).join("/");
  const target = backendBase() + "/api/" + path + request.nextUrl.search;
  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("content-length");
  headers.delete("connection");
  headers.delete("accept-encoding");

  const method = request.method.toUpperCase();
  const body = method === "GET" || method === "HEAD" ? undefined : await request.arrayBuffer();

  try {
    const upstream = await fetch(target, {
      method,
      headers,
      body,
      cache: "no-store",
      redirect: "manual"
    });
    const responseHeaders = new Headers(upstream.headers);
    responseHeaders.delete("content-encoding");
    responseHeaders.delete("content-length");
    responseHeaders.delete("transfer-encoding");
    responseHeaders.set("cache-control", "no-store");
    return new Response(method === "HEAD" ? null : upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: responseHeaders
    });
  } catch {
    return Response.json({ detail: "UniverseAI API is temporarily unavailable. Please try again." }, { status: 502 });
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
export const OPTIONS = proxy;
