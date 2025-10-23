export interface DocumentMeta {
  id: number;
  type: string;
  storage_uri: string;
  has_text: boolean;
}
export interface DocumentText {
  id: number;
  text: string;
}

export interface SearchHit {
  id: number;
  storage_uri: string;
  snippet: string;
  distance: number;
  score: number;
  bm25: number;
}
export interface SearchResponse {
  query: string;
  results: SearchHit[];
  next_offset: number | null;
}
export interface UploadResponse {
  id: string;
  sha256: string;
  uri: string;
}
