import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { V2Layout } from "@/v2/components/V2Layout";
import { V2Button } from "@/v2/components/V2Button";
import { V2Loader } from "@/v2/components/V2Loader";
import { GuidanceResults } from "@/v2/components/consultation/GuidanceResults";
import { useSessionDetail } from "@/v2/hooks/useSessionHistory";
import { mapStoredResultsToGuidance } from "@/v2/lib/guidanceMapper";
import { deleteSession } from "@/v2/lib/sessionsApi";
import { formatSessionDate, statusLabel } from "@/v2/lib/sessionFormat";

export default function ConsultationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { session, results, isLoading, error } = useSessionDetail(id);
  const guidance = mapStoredResultsToGuidance(results);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    if (!id || !session) return;
    const title = session.title || "Health consultation";
    const ok = window.confirm(
      `Delete “${title}”? This cannot be undone.`,
    );
    if (!ok) return;

    setIsDeleting(true);
    try {
      await deleteSession(id);
      toast.success("Consultation deleted");
      navigate("/consultations", { replace: true });
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Couldn't delete this consultation",
      );
      setIsDeleting(false);
    }
  };

  return (
    <V2Layout footer="compact">
      <div className="mx-auto flex w-full max-w-page flex-1 flex-col px-5 py-5 md:px-8 md:py-6 lg:px-12">
        <div className="mb-4 flex flex-wrap items-end justify-between gap-3 border-b border-healia-border-subtle pb-4">
          <div className="min-w-0">
            <Link
              to="/consultations"
              className="text-xs font-medium text-healia-brand hover:underline"
            >
              ← Past consultations
            </Link>
            <h1 className="mt-2 truncate text-xl font-semibold tracking-tight text-healia-text md:text-2xl">
              {isLoading ? "Loading consultation…" : session?.title || "Health consultation"}
            </h1>
            {session ? (
              <p className="mt-1 text-xs text-healia-text-muted">
                {formatSessionDate(session.started_at)} ·{" "}
                {statusLabel(session.status)}
              </p>
            ) : null}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {session ? (
              <V2Button
                variant="secondary"
                disabled={isDeleting}
                onClick={() => void handleDelete()}
                className="px-4 py-2 text-sm text-healia-danger hover:bg-healia-danger/[0.06]"
              >
                {isDeleting ? "Deleting…" : "Delete"}
              </V2Button>
            ) : null}
            <V2Button to="/consultation" className="px-4 py-2 text-sm">
              New consultation
            </V2Button>
          </div>
        </div>

        {isLoading ? (
          <V2Loader full label="Loading guidance…" />
        ) : error ? (
          <p className="rounded-lg border border-healia-danger/20 bg-healia-danger/[0.04] px-4 py-3 text-sm text-healia-danger">
            {error}
          </p>
        ) : !guidance ? (
          <div className="flex flex-1 items-center justify-center">
            <p className="text-sm text-healia-text-secondary">
              No guidance was saved for this consultation yet.
            </p>
          </div>
        ) : (
          <GuidanceResults guidance={guidance} />
        )}

        <p className="mt-4 text-xs leading-relaxed text-healia-text-muted">
          Educational guidance only — not a medical diagnosis or treatment plan.
        </p>
      </div>
    </V2Layout>
  );
}
