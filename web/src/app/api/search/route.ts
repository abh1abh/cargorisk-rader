import { NextRequest, NextResponse } from "next/server";
import { api } from "@/lib/api"; // safe here, server-only

// API route for /api/search (proxy to FastAPI /search)
export async function GET(req: NextRequest) {
    const { searchParams } = new URL(req.url);
    const q = searchParams.get("q") ?? "";
    const limit = searchParams.get("limit") ?? "20";
    const offset = searchParams.get("offset") ?? "0";

    try {
        // Call FastAPI using your server-only api() helper
        const data = await api(`/search?q=${encodeURIComponent(q)}&limit=${limit}&offset=${offset}`);
        return NextResponse.json(data);
    } catch (err: unknown) {
        if (err instanceof Error) {
            return NextResponse.json({ error: err.message }, { status: 500 });
        }
        return NextResponse.json({ error: "Unknown error" }, { status: 500 });
    }
}
