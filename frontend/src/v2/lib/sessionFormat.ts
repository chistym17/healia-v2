function formatSessionDate(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function statusLabel(status: string) {
  switch (status) {
    case "completed":
      return "Completed";
    case "processing":
      return "Processing";
    case "in_progress":
      return "In progress";
    case "failed":
      return "Failed";
    default:
      return "Started";
  }
}

export { formatSessionDate, statusLabel };
