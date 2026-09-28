import type { ProcessingStep } from "@/v2/types/consultation";

export type PipelineEvent = {
  type?: string;
  session_id?: string;
  turn_id?: string;
  phase?: string;
  status?: string;
  message?: string;
  data?: Record<string, unknown>;
  elapsed_ms?: number;
};

export const LIVE_PROCESSING_STEPS: ProcessingStep[] = [
  { id: "symptoms", label: "Reviewing your symptoms" },
  { id: "references", label: "Checking medical references" },
  { id: "results", label: "Preparing your results" },
];

export function stepIdForPipelinePhase(phase: string | undefined): string | null {
  switch (phase) {
    case "case_package":
    case "assessment_rag":
    case "turn":
    case "supervisor":
      return "symptoms";
    case "knowledge_rag":
      return "references";
    case "guidance":
    case "speech":
      return "results";
    default:
      return null;
  }
}

export function isGuidanceReadyEvent(event: PipelineEvent): boolean {
  return event.phase === "guidance" && event.status === "completed";
}

export function isSpeechCompleteEvent(event: PipelineEvent): boolean {
  return event.phase === "speech" && event.status === "completed";
}

/** Agent / supervisor decided there isn't enough patient info for guidance. */
export function isInsufficientInfoEvent(event: PipelineEvent): boolean {
  if (event.phase === "session" && event.status === "insufficient") return true;
  if (
    event.phase === "case_package" &&
    event.status === "completed" &&
    event.data?.ready_for_retrieval === false
  ) {
    return true;
  }
  return false;
}

export function isProcessingStartEvent(event: PipelineEvent): boolean {
  if (isInsufficientInfoEvent(event)) return false;
  if (event.phase === "case_package" && event.status === "completed") {
    // Only enter processing when retrieval can actually run.
    if (event.data?.ready_for_retrieval === false) return false;
    return true;
  }
  if (event.phase === "knowledge_rag" && event.status === "started") return true;
  if (
    event.phase === "supervisor" &&
    event.status === "completed" &&
    event.data?.action === "build_final_query"
  ) {
    return true;
  }
  return false;
}

export function parsePipelinePayload(raw: Uint8Array): PipelineEvent | null {
  try {
    const text = new TextDecoder().decode(raw);
    const parsed = JSON.parse(text) as PipelineEvent;
    if (!parsed || typeof parsed !== "object") return null;
    return parsed;
  } catch {
    return null;
  }
}
