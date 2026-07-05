export interface Source {
  text: string;
  page: number | string;
  chunk: number;
  document?: string;
}

export interface Metrics {
  response_time_ms: number;
  // Retrieval stage counts
  faiss_chunks: number;
  bm25_chunks: number;
  total_retrieved: number;
  after_filter: number;
  after_dedup: number;
  after_rerank: number;
  // Context compression
  context_chars_before: number;
  context_chars_after: number;
  compression_ratio: number;
  filter_applied: boolean;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  metrics?: Metrics;
}
