export type DocumentMeta = {
  id: number;
  type: string;
  storage_uri: string;
  has_text: boolean;
};
export type DocumentText = { id: number; text: string };
export type SearchHit = { id: number; storage_uri: string; snippet: string };
export type SearchResponse = { query: string; results: SearchHit[]; total: number };
export type UploadResponse = { id: string; sha256: string; uri: string };
