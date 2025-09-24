"use client";
import { useEffect, useState } from "react";
export default function Health() {
    const [data, setData] = useState<Record<string, unknown> | null>(null);
    // const api = process.env.NEXT_PUBLIC_API_URL;
    // console.log(api);
    useEffect(() => {
        const ctrl = new AbortController();
        fetch("/api/health", { signal: ctrl.signal })
            .then((r) => r.json())
            .then(setData)
            .catch(() => {});
        return () => ctrl.abort();
    }, []);
    return <pre className="p-4">{JSON.stringify(data, null, 2)}</pre>;
}
