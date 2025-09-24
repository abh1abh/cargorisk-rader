"use client";
import { UploadResponse } from "@/types";
import { useRef, useState } from "react";

// type UploadResponse = { id: string; sha256: string; uri: string };

export default function Upload() {
    const [result, setResult] = useState<UploadResponse | null>(null);
    const [err, setErr] = useState<string | null>(null);
    const [busy, setBusy] = useState(false);
    const abortRef = useRef<AbortController | null>(null);

    async function onClick(e: React.ChangeEvent<HTMLInputElement>) {
        const f = e.target.files?.[0];
        if (!f) return;

        // cancel any in-flight upload
        abortRef.current?.abort();
        const ctrl = new AbortController();
        abortRef.current = ctrl;

        const fd = new FormData();
        fd.append("file", f);

        setBusy(true);
        setErr(null);
        setResult(null);

        try {
            const r = await fetch("/api/upload", { method: "POST", body: fd, signal: ctrl.signal });
            if (!r.ok) {
                const msg = await r.text().catch(() => "");
                throw new Error(msg || `HTTP ${r.status}`);
            }
            setResult(await r.json());
        } catch (e: any) {
            if (e?.name !== "AbortError") setErr(e?.message || "Upload failed");
        } finally {
            setBusy(false);
        }
    }
    return (
        <div className="p-6 w-full h-full">
            <input
                className="
                    text-sm text-grey-500
                    file:mr-5 file:py-3 file:px-10
                    file:rounded-full file:border-0
                    file:text-md file:font-semibold  file:text-white
                    file:bg-gradient-to-r file:from-blue-600 file:to-amber-600
                    hover:file:cursor-pointer hover:file:opacity-80
                "
                type="file"
                disabled={busy}
                onChange={onClick}
            />
            {busy && <div className="mt-3 text-sm text-gray-600">Uploading…</div>}
            {err && <pre className="mt-3 text-red-700 bg-red-50 border border-red-200 rounded p-2">{err}</pre>}
            {result && <pre className="mt-3">{JSON.stringify(result, null, 2)}</pre>}
        </div>
    );
}
