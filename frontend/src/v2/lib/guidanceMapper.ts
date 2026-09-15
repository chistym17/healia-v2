import type { GuidanceReference, GuidanceResult } from "@/v2/types/consultation";

/** Backend guidance / pipeline `results` payload. */
export type BackendGuidancePayload = {
  summary?: string;
  possible_concerns?: string;
  possibleConcerns?: string;
  actions?: string[];
  warning_signs?: string;
  warningSigns?: string;
  seek_care?: string;
  seekCare?: string;
  spoken_answer?: string;
  detailed_answer?: string;
  citations?: Array<{
    index?: number;
    source?: string;
    topic?: string;
    section?: string;
  }>;
  confidence?: string;
};

export function mapBackendGuidanceToResult(
  payload: BackendGuidancePayload | null | undefined,
): GuidanceResult | null {
  if (!payload) return null;

  const summary =
    (payload.summary || payload.detailed_answer || payload.spoken_answer || "").trim();
  const possibleConcerns = (
    payload.possible_concerns ||
    payload.possibleConcerns ||
    payload.detailed_answer ||
    summary
  ).trim();
  const warningSigns = (
    payload.warning_signs ||
    payload.warningSigns ||
    "Seek urgent care for severe or sudden symptoms, difficulty breathing, chest pain, confusion, or rapidly worsening condition."
  ).trim();
  const seekCare = (
    payload.seek_care ||
    payload.seekCare ||
    "See a qualified clinician if symptoms persist, worsen, or you are unsure. For emergencies, seek urgent care immediately."
  ).trim();

  const actions = Array.isArray(payload.actions)
    ? payload.actions.map((a) => String(a).trim()).filter(Boolean)
    : [];

  const references: GuidanceReference[] = Array.isArray(payload.citations)
    ? payload.citations.map((c) => ({
        source: String(c.source || "Medical reference").trim(),
        title: [c.topic, c.section].filter(Boolean).join(" — ") || "Reference",
      }))
    : [];

  if (!summary && actions.length === 0) return null;

  return {
    summary: summary || "Based on what you shared, here is educational guidance.",
    possibleConcerns:
      possibleConcerns ||
      "Several possibilities may fit your symptoms. This is not a diagnosis.",
    actions:
      actions.length > 0
        ? actions
        : [
            "Rest and monitor your symptoms",
            "Stay hydrated",
            "Seek medical care if symptoms worsen",
          ],
    warningSigns,
    seekCare,
    references,
  };
}
