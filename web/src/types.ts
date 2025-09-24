export type DocumentMeta = {
    id: number;
    type: string;
    storage_uri: string;
    has_text: boolean;
};

export type DocumentText = { id: number; text: string };

export type SearchHit = { id: number; storage_uri: string; snippet: string };
export type SearchResponse = { results: SearchHit[]; total: number };
