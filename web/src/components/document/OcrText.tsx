"use client";

interface Props {
  text: string;
}

// Client component to handle onClick + clipboard
export default function OcrText({ text }: Props) {
  async function copy() {
    await navigator.clipboard.writeText(text || "");
    alert("Copied OCR text");
  }

  return (
    <div className="relative">
      <div className="flex items-center justify-between mb-2">
        <h2 className="font-medium">OCR Text</h2>
        <button onClick={copy} className="px-2 py-1 text-sm border rounded">
          Copy
        </button>
      </div>
      <pre className="p-4 bg-gray-50 border rounded overflow-auto max-h-[70vh] whitespace-pre-wrap text-sm">
        {text || "—"}
      </pre>
    </div>
  );
}
