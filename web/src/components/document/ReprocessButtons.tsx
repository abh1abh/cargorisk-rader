"use client";
import { useState } from "react";
import { Button } from "../ui/Button";
export function ReprocessButtons({ id }: { id: number }) {
  const [loading, setLoading] = useState<null | "ocr" | "embed">(null);
  const [error, setError] = useState<string | null>(null);

  async function reprocess(path: string) {
    setLoading(path.includes("ocr") ? "ocr" : "embed");
    try {
      await fetch(`/api/document/${id}/${path}`, { method: "POST" });
    } catch (e) {
      const err = e as Error;
      setError(err.message);
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="flex gap-2">
      <Button onClick={() => reprocess("ocr")} disabled={loading !== null} variant="primary">
        {loading === "ocr" ? "Re-OCR.." : "RE-OCR"}
      </Button>
      <Button onClick={() => reprocess("embed")} disabled={loading !== null} variant="primary">
        {loading === "ocr" ? "Re-Embed.." : "RE-Embed"}
      </Button>
      {error && <span className="text-sm text-red-600">{error}</span>}
    </div>
  );
}
