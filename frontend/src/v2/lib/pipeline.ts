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

export function isProcessingStartEvent(event: PipelineEvent): boolean {
  if (event.phase === "case_package" && event.status === "completed") return true;
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
