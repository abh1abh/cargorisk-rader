"use client";
import { useEffect, useState } from "react";
export default function Health() {
    const [data, setData] = useState<any>(null);
    const api = process.env.NEXT_PUBLIC_API_URL;
    console.log(api);
    useEffect(() => {
        fetch(`${api}/health`)
            .then((r) => r.json())
            .then(setData);
    }, []);
    return <pre className="p-4">{JSON.stringify(data, null, 2)}</pre>;
}
