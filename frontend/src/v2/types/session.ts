export type SessionStatus =
  | "started"
  | "in_progress"
  | "processing"
  | "completed"
  | "failed";

export type StoredTranscriptMessage = {
  role: "user" | "healia";
  text: string;
  ts?: string | null;
};

export type SessionSummary = {
  id: string;
  user_id: string;
  livekit_room_name: string | null;
  livekit_session_id: string | null;
  status: SessionStatus;
  title: string | null;
  started_at: string;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  has_results: boolean;
};

export type SessionRecord = SessionSummary & {
  transcript: StoredTranscriptMessage[];
};

export type StoredSessionResults = {
  id: string;
  session_id: string;
  summary: string;
  possible_concerns: string;
  actions: string[];
  warning_signs: string;
  seek_care: string;
  references: Array<{ source: string; title: string }>;
  spoken_answer: string | null;
  confidence: string | null;
  created_at: string;
  updated_at: string;
};

export type CompleteSessionPayload = {
  title?: string;
  transcript: StoredTranscriptMessage[];
  results: {
    summary: string;
    possible_concerns: string;
    actions: string[];
    warning_signs: string;
    seek_care: string;
    references: Array<{ source: string; title: string }>;
    spoken_answer?: string | null;
    confidence?: string | null;
  };
};
