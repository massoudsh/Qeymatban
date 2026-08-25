import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  const apiUrl = process.env.QEYMATBAN_API_URL ?? "http://localhost:8000";
  try {
    const response = await fetch(`${apiUrl}/v1/valuations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(process.env.QEYMATBAN_API_KEY ? { "X-API-Key": process.env.QEYMATBAN_API_KEY } : {}),
      },
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
