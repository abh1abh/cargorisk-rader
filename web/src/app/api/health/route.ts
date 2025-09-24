import { NextResponse } from "next/server";
import { api } from "@/lib/api"; // safe here, server-only

// API route for /api/search (proxy to FastAPI /search)
export async function GET() {
    try {
        // Call FastAPI using your server-only api() helper
        const data = await api(`/health`);
        return NextResponse.json(data);
    } catch (err: unknown) {
        if (err instanceof Error) {
            return NextResponse.json({ error: err.message }, { status: 500 });
        }
        return NextResponse.json({ error: "Unknown error" }, { status: 500 });
    }
}
