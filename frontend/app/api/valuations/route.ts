import { NextRequest, NextResponse } from "next/server";

const apiHeaders = () => ({
  "Content-Type": "application/json",
  ...(process.env.QEYMATBAN_API_KEY ? { "X-API-Key": process.env.QEYMATBAN_API_KEY } : {}),
});

export async function GET(request: NextRequest) {
  const apiUrl = process.env.QEYMATBAN_API_URL ?? "http://localhost:8000";
  try {
    const response = await fetch(`${apiUrl}/v1/valuations${request.nextUrl.search}`, {
      headers: apiHeaders(),
      cache: "no-store",
    });
    return new NextResponse(await response.text(), {
      status: response.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch {
    return NextResponse.json({ detail: "سرویس ارزش‌گذاری در دسترس نیست" }, { status: 503 });
  }
}

export async function POST(request: NextRequest) {
  const apiUrl = process.env.QEYMATBAN_API_URL ?? "http://localhost:8000";
  try {
    const response = await fetch(`${apiUrl}/v1/valuations`, {
      method: "POST",
      headers: apiHeaders(),
      body: await request.text(),
      cache: "no-store",
    });
    return new NextResponse(await response.text(), {
      status: response.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch {
    return NextResponse.json({ detail: "سرویس ارزش‌گذاری در دسترس نیست" }, { status: 503 });
  }
}
