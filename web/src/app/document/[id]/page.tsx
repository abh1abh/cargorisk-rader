import { api } from "@/lib/api";
import type { DocumentMeta, DocumentText } from "@/types";
import OcrText from "@/components/OcrText";

async function getDoc(id: string) {
  const [meta, text] = await Promise.all([
    api<DocumentMeta>(`/document/${id}`),
    api<DocumentText>(`/document/${id}/text`).catch(() => ({ id: Number(id), text: "" })),
  ]);
  return { meta, text: text.text || "" };
}

export const runtime = "nodejs"; // optional, keeps it off Edge

// Server component for Doc page
// (uses server-side api() wrapper, and renders client OcrText component)
export default async function DocPage({ params }: { params: { id: string } }) {
  const { meta, text } = await getDoc(params.id);

  return (
    <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="space-y-3">
        <h1 className="text-xl font-semibold">Document #{meta.id}</h1>
        <div className="text-sm">
          Type: <span className="font-mono">{meta.type}</span>
        </div>
        <div className="text-sm break-all">
          Storage:{" "}
          <a className="underline" href={`/api/document/${meta.id}/download`} target="_blank" rel="noreferrer">
            Open original
          </a>
        </div>
        <div className="pt-2">
          <a className="underline" href="/upload">
            Upload another
          </a>
        </div>
        {!meta.has_text && (
          <div className="text-amber-700 bg-amber-50 border border-amber-200 rounded p-2 text-sm">
            OCR text not available yet for this document.
          </div>
        )}
      </div>

      {/* Client component handles onClick + clipboard */}
      <OcrText text={text} />
    </div>
  );
}
