import {
  MOCK_GUIDANCE,
  MOCK_PROCESSING_STEPS,
  MOCK_DELAYS,
} from "@/v2/data/mockConsultation";
import type { GuidanceResult, ProcessingStep } from "@/v2/types/consultation";
import { LIVE_PROCESSING_STEPS } from "@/v2/lib/pipeline";

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Offline mock processing. Live path uses pipeline events from LiveKit.
 */
export async function mockRunProcessing(
  onStepComplete: (stepId: string) => void,
): Promise<GuidanceResult> {
  for (const step of MOCK_PROCESSING_STEPS) {
    await delay(MOCK_DELAYS.processingStep);
    onStepComplete(step.id);
  }
  return MOCK_GUIDANCE;
}

export function mockGetProcessingSteps(): ProcessingStep[] {
  return LIVE_PROCESSING_STEPS;
}
