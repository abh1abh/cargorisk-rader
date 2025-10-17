export type DocumentMeta = {
  id: number;
  type: string;
  storage_uri: string;
  has_text: boolean;
};
export type DocumentText = { id: number; text: string };
export type SearchHit = {
  id: number;
  storage_uri: string;
  snippet: string;
  distance: number;
  score: number;
  bm25: number;
};
export type SearchResponse = { query: string; results: SearchHit[]; next_offset: number | null };
export type UploadResponse = { id: string; sha256: string; uri: string };
