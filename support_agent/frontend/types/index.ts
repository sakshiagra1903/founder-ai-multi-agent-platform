export interface User {
  id: string;
  name: string;
  email: string;
  created_at: string;
}

export interface Document {
  id: string;
  user_id: string;
  filename: string;
  file_path: string;
  file_size: number;
  status: 'processing' | 'processed' | 'failed';
  created_at: string;
}

export interface SourceCitation {
  document: string;
  page: number;
  type?: 'document' | 'web';
  url?: string | null;
}

export interface TicketInfo {
  id: string;
  subject: string;
  status: string;
}

export interface Ticket {
  id: string;
  subject: string;
  description: string;
  source_question?: string | null;
  status: string;
  created_at: string;
}

// Live agent activity shown while streaming (e.g. "Searching documents...")
export interface AgentActivity {
  tool: string;
  label: string;
  status: 'running' | 'done';
}

// Raw SSE event shapes emitted by POST /chat/stream
export type ChatStreamEvent =
  | { type: 'tool_start'; tool: string; input?: any }
  | { type: 'tool_end'; tool: string }
  | { type: 'token'; content: string }
  | { type: 'sources'; sources: SourceCitation[] }
  | { type: 'ticket'; ticket: TicketInfo }
  | { type: 'error'; message: string }
  | { type: 'done'; answer: string };

export interface ChatHistoryEntry {
  id: string;
  question: string;
  answer: string;
  sources: SourceCitation[] | null;
  timestamp: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceCitation[];
  ticket?: TicketInfo | null;
  activities?: AgentActivity[];
  isStreaming?: boolean;
  timestamp: Date;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
