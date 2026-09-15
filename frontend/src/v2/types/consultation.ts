export type VoiceState =
  | "ready"
  | "listening"
  | "thinking"
  | "speaking"
  | "error";

export type TranscriptRole = "user" | "healia";

export type TranscriptMessage = {
  id: string;
  role: TranscriptRole;
  text: string;
};

export type GuidanceReference = {
  source: string;
  title: string;
};

export type GuidanceResult = {
  summary: string;
  possibleConcerns: string;
  actions: string[];
  warningSigns: string;
  seekCare: string;
  references: GuidanceReference[];
};

export type ProcessingStep = {
  id: string;
  label: string;
};

export type ConsultationPhase =
  | "prep"
  | "session"
  | "processing"
  | "results";
