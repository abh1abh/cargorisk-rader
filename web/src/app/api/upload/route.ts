import { NextRequest, NextResponse } from "next/server";

// API route for /api/search (proxy to FastAPI /search)
export async function POST(req: NextRequest) {
    try {
        const formData = await req.formData();

        const response = await fetch(`${process.env.INTERNAL_API_URL || "http://api:8000"}/upload`, {
            method: "POST",
            body: formData,
        });

        const contentType = response.headers.get("Content-Type") || "";
        if (contentType.includes("application/json")) {
            const data = await response.json();
            return NextResponse.json(data, { status: response.status });
        } else {
            const text = await response.text();
            return NextResponse.json({ error: text }, { status: response.status });
        }
    } catch (err: unknown) {
        if (err instanceof Error) {
            return NextResponse.json({ error: err.message }, { status: 500 });
        }
        return NextResponse.json({ error: "Unknown error" }, { status: 500 });
    }
}
