export interface Source {
  text: string;
  page: number | string;
  chunk: number;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}