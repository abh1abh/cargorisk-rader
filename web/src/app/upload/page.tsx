"use client";
import { useState } from "react";

type UploadResponse = { id: string; sha256: string; uri: string };

export default function Upload() {
    const [res, setRes] = useState<UploadResponse | null>(null);
    const api = process.env.NEXT_PUBLIC_API_URL;
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
                onChange={async (e) => {
                    const f = e.target.files?.[0];
                    if (!f) return;
                    const fd = new FormData();
                    fd.append("file", f);
                    const r = await fetch(`${api}/upload`, { method: "POST", body: fd });
                    setRes(await r.json());
                }}
            />
            {res ? <pre className="mt-4">{JSON.stringify(res, null, 2)}</pre> : <pre className="mt-4">upload</pre>}
        </div>
    );
}
