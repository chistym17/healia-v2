export type ConsultationErrorKind =
  | "mic_permission"
  | "network"
  | "auth"
  | "service"
  | "unknown";

export type ConsultationError = {
  kind: ConsultationErrorKind;
  title: string;
  message: string;
  fix: string;
};

const ERRORS: Record<ConsultationErrorKind, ConsultationError> = {
  mic_permission: {
    kind: "mic_permission",
    title: "Microphone access needed",
    message:
      "Healia couldn't use your microphone, so the consultation couldn't start.",
    fix: "Allow microphone access for this site in your browser settings, then try again. On some phones, also check that the app or browser has mic permission in system settings.",
  },
  network: {
    kind: "network",
    title: "Connection problem",
    message:
      "We couldn't reach Healia. This is usually a network issue on your side or a temporary outage.",
    fix: "Check your internet connection, then try again. If you're on a VPN or restricted network, try without it.",
  },
  auth: {
    kind: "auth",
    title: "Sign-in required",
    message: "Your session expired or you're not signed in, so voice consultation couldn't start.",
    fix: "Sign in again, then return here and start a new consultation.",
  },
  service: {
    kind: "service",
    title: "Healia is temporarily unavailable",
    message:
      "Something went wrong on our side while starting or running your consultation.",
    fix: "Wait a moment and try again. If it keeps happening, come back later — no need to keep retrying repeatedly.",
  },
  unknown: {
    kind: "unknown",
    title: "Couldn't continue the consultation",
    message: "Something unexpected interrupted your consultation.",
    fix: "Try again once. If it still fails, refresh the page or start a new consultation from the beginning.",
  },
};

function errorText(error: unknown): string {
  if (!error) return "";
  if (typeof error === "string") return error;
  if (error instanceof Error) {
    return `${error.name} ${error.message}`;
  }
  if (typeof error === "object") {
    const record = error as Record<string, unknown>;
    const parts = [record.name, record.message, record.reason, record.code]
      .filter((v) => typeof v === "string" || typeof v === "number")
      .map(String);
    return parts.join(" ");
  }
  return String(error);
}

export function consultationErrorFromKind(
  kind: ConsultationErrorKind,
): ConsultationError {
  return { ...ERRORS[kind] };
}

/**
 * Map raw LiveKit / browser / fetch failures to calm user-facing copy.
 * Never expose stack traces or internal service names.
 */
export function classifyConsultationError(error: unknown): ConsultationError {
  const text = errorText(error).toLowerCase();

  if (
    text.includes("notallowed") ||
    text.includes("permission denied") ||
    text.includes("permissiondenied") ||
    text.includes("getusermedia") ||
    text.includes("microphone") ||
    text.includes("mic ") ||
    text.includes("audio capture") ||
    text.includes("devices error")
  ) {
    return consultationErrorFromKind("mic_permission");
  }

  if (
    text.includes("not signed in") ||
    text.includes("unauthorized") ||
    text.includes("401") ||
    text.includes("403") ||
    text.includes("jwt") ||
    (text.includes("token") && text.includes("invalid"))
  ) {
    return consultationErrorFromKind("auth");
  }

  if (
    text.includes("failed to fetch") ||
    text.includes("networkerror") ||
    text.includes("network request failed") ||
    text.includes("offline") ||
    text.includes("timeout") ||
    text.includes("timed out") ||
    text.includes("err_network") ||
    text.includes("connection refused") ||
    text.includes("dns")
  ) {
    return consultationErrorFromKind("network");
  }

  if (
    text.includes("503") ||
    text.includes("502") ||
    text.includes("500") ||
    text.includes("agent") ||
    text.includes("livekit") ||
    text.includes("server")
  ) {
    return consultationErrorFromKind("service");
  }

  return consultationErrorFromKind("unknown");
}
