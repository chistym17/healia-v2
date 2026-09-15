import type {
  GuidanceResult,
  ProcessingStep,
  TranscriptMessage,
} from "@/v2/types/consultation";

export const MOCK_GREETING: TranscriptMessage = {
  id: "greeting",
  role: "healia",
  text: "Tell me what you're feeling today.",
};

export const MOCK_USER_TURN: TranscriptMessage = {
  id: "user-1",
  role: "user",
  text: "I've had a headache since this morning, mostly on the left side.",
};

export const MOCK_HEALIA_FOLLOWUP: TranscriptMessage = {
  id: "healia-1",
  role: "healia",
  text: "Any nausea, fever, or changes in your vision?",
};

export const MOCK_USER_FOLLOWUP: TranscriptMessage = {
  id: "user-2",
  role: "user",
  text: "No fever. A little nausea when the pain is worse.",
};

export const MOCK_HEALIA_CLOSE: TranscriptMessage = {
  id: "healia-2",
  role: "healia",
  text: "Thank you. I have enough to prepare your guidance.",
};

export const MOCK_PROCESSING_STEPS: ProcessingStep[] = [
  { id: "symptoms", label: "Reviewing your symptoms" },
  { id: "references", label: "Checking medical references" },
  { id: "results", label: "Preparing your results" },
];

export const MOCK_GUIDANCE: GuidanceResult = {
  summary:
    "You described a left-sided headache since this morning with occasional nausea and no fever.",
  possibleConcerns:
    "This may be consistent with a mild tension-type or migraine headache. Other causes are possible and cannot be ruled out without an exam.",
  actions: [
    "Rest in a quiet, dimly lit room",
    "Drink water and consider an OTC pain reliever if you usually tolerate them",
    "Track whether symptoms change over the next 24 hours",
  ],
  warningSigns:
    "Sudden severe headache, confusion, weakness, vision loss, neck stiffness, or fever with headache.",
  seekCare:
    "Seek prompt care if warning signs appear. See a clinician if symptoms persist beyond 48 hours or worsen.",
  references: [
    {
      source: "Mayo Clinic",
      title: "Tension headache — symptoms & causes",
    },
    {
      source: "NHS",
      title: "Headaches — overview and self-care",
    },
    {
      source: "MedlinePlus",
      title: "When to worry about a headache",
    },
  ],
};

/** Simulated delay (ms) — swap for real API latency later. */
export const MOCK_DELAYS = {
  thinking: 1200,
  speaking: 1800,
  processingStep: 1400,
} as const;
