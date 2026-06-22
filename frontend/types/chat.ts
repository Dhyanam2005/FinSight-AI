export interface Source {
  text: string;
  page: number | string;
  chunk: number;
}

export interface Metrics {
  response_time_ms: number;
  chunks_retrieved: number;
  compression_ratio: number;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  metrics?: Metrics;
}