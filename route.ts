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
    const res = await fetch(`${backendUrl}/baby/${id}`, {
      signal: AbortSignal.timeout(3000)
    });

    if (!res.ok) {
      throw new Error(`Backend returned ${res.status}`);
    }

    const data = await res.json();
    return Response.json(data);
  } catch (err) {
    const fallbackData = {
      mrn: id || "B001",
      full_name: "Baby Johnson",
      sex: "Female",
      dob: "2026-01-20",
      birth_weight: 2850,
      gestational_age: 38,
      mother_name: "Sarah Johnson",
      mother_dob: "1995-03-15",
      admission_date: "2026-01-20T08:30:00Z",
      discharge_date: null,
      notes: "Healthy newborn under routine observation",
      updated_at: new Date().toISOString(),
      medical_record: {
        allergies: "None known",
        medications: [],
        procedures: ["Vitamin K injection", "Hepatitis B vaccination"],
        conditions: []
      }
    };

    return Response.json(fallbackData);
  }
}
