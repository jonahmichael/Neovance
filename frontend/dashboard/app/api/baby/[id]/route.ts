import { NextResponse } from 'next/server';

// app/api/baby/[id]/route.ts

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  const backendUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  try {
    const res = await fetch(`${backendUrl}/baby/${id}`);

    if (!res.ok) {
      return Response.json(
        { error: "Backend error" },
        { status: res.status }
      );
    }

    const data = await res.json();
    return Response.json(data);
  } catch (err) {
    console.error("API error:", err);
    return Response.json(
      { error: "Failed to reach backend" },
      { status: 500 }
    );
  }
}
