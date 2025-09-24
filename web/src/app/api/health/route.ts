import { NextRequest, NextResponse } from "next/server";
import { api } from "@/lib/api"; // safe here, server-only

// API route for /api/search (proxy to FastAPI /search)
export async function GET(req: NextRequest) {
    try {
        // Call FastAPI using your server-only api() helper
        const data = await api(`/health`);
        return NextResponse.json(data);
    } catch (err: any) {
        return NextResponse.json({ error: err.message }, { status: 500 });
    }
}
