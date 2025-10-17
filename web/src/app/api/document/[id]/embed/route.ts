import { api } from "@/lib/api";
import { NextRequest, NextResponse } from "next/server";

type EmbedResponse = { id: number; dim: number };

export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params;
    console.log("[embed route] handling id=", id);

    const response = await api<EmbedResponse>(`/document/${id}/embed`, {
      method: "POST",
    });

    return NextResponse.json(response);
  } catch (err: unknown) {
    if (err instanceof Error) {
      return NextResponse.json({ error: err.message }, { status: 500 });
    }
    return NextResponse.json({ error: "Unknown error" }, { status: 500 });
  }
}
