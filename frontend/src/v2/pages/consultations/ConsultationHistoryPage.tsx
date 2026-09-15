import { Link } from "react-router-dom";
import { ChevronRight, Inbox, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { V2Layout } from "@/v2/components/V2Layout";
import { V2Button } from "@/v2/components/V2Button";
import { V2Loader } from "@/v2/components/V2Loader";
import { useSessionHistory } from "@/v2/hooks/useSessionHistory";
import { formatSessionDate, statusLabel } from "@/v2/lib/sessionFormat";

export default function ConsultationHistoryPage() {
  const { sessions, isLoading, error, reload, removeSession, deletingId } =
    useSessionHistory();

  const handleDelete = async (sessionId: string, title: string) => {
    const ok = window.confirm(
      `Delete “${title || "Health consultation"}”? This cannot be undone.`,
    );
    if (!ok) return;
    try {
      await removeSession(sessionId);
      toast.success("Consultation deleted");
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Couldn't delete this consultation",
      );
    }
  };

  return (
    <V2Layout footer="compact">
      <div className="mx-auto flex w-full max-w-page flex-1 flex-col px-5 py-8 md:px-8 md:py-10 lg:px-12">
        <div className="flex flex-wrap items-end justify-between gap-4 border-b border-healia-border-subtle pb-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-healia-brand">
              Your account
            </p>
            <h1 className="mt-2 text-2xl font-semibold tracking-tight text-healia-text md:text-3xl">
              Past consultations
            </h1>
            <p className="mt-2 max-w-lg text-sm text-healia-text-secondary">
              Reopen guidance from earlier sessions. Private to you.
            </p>
          </div>
          <V2Button to="/consultation" className="px-5 py-2.5 text-sm">
            New consultation
          </V2Button>
        </div>

        <div className="mt-6 min-h-0 flex-1">
          {isLoading ? (
            <V2Loader full label="Loading your consultations…" />
          ) : error ? (
            <div className="mx-auto max-w-md rounded-xl border border-healia-danger/20 bg-healia-danger/[0.04] px-5 py-6 text-center">
              <p className="text-sm text-healia-danger">{error}</p>
              <button
                type="button"
                onClick={() => void reload()}
                className="mt-3 text-sm font-medium text-healia-brand hover:underline"
              >
                Try again
              </button>
            </div>
          ) : sessions.length === 0 ? (
            <div className="mx-auto flex max-w-md flex-col items-center rounded-xl border border-dashed border-healia-border bg-healia-bg-secondary/60 px-6 py-12 text-center">
              <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-healia-brand-light text-healia-brand">
                <Inbox className="h-5 w-5" strokeWidth={1.75} />
              </span>
              <p className="mt-4 text-base font-medium text-healia-text">
                No consultations yet
              </p>
              <p className="mt-1.5 text-sm text-healia-text-secondary">
                Start a voice consultation and your guidance will appear here.
              </p>
              <div className="mt-6">
                <V2Button to="/consultation" className="px-5 py-2.5 text-sm">
                  Start consultation
                </V2Button>
              </div>
            </div>
          ) : (
            <ul className="divide-y divide-healia-border-subtle overflow-hidden rounded-xl border border-healia-border bg-healia-bg-secondary">
              {sessions.map((session) => {
                const title = session.title || "Health consultation";
                const isDeleting = deletingId === session.id;
                return (
                  <li key={session.id} className="flex items-stretch">
                    <Link
                      to={`/consultations/${session.id}`}
                      className="group flex min-w-0 flex-1 items-center justify-between gap-4 px-4 py-3.5 transition-colors hover:bg-healia-brand-light/40 md:px-5"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-healia-text md:text-base">
                          {title}
                        </p>
                        <p className="mt-0.5 text-xs text-healia-text-muted">
                          {formatSessionDate(session.started_at)}
                        </p>
                      </div>
                      <div className="flex shrink-0 items-center gap-2.5">
                        <span
                          className={`rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${
                            session.status === "completed"
                              ? "bg-healia-success/10 text-healia-success"
                              : "bg-healia-brand-light text-healia-brand"
                          }`}
                        >
                          {statusLabel(session.status)}
                        </span>
                        <ChevronRight
                          className="h-4 w-4 text-healia-text-muted transition-transform group-hover:translate-x-0.5 group-hover:text-healia-brand"
                          strokeWidth={1.75}
                        />
                      </div>
                    </Link>
                    <button
                      type="button"
                      aria-label={`Delete ${title}`}
                      disabled={isDeleting}
                      onClick={() => void handleDelete(session.id, title)}
                      className="flex shrink-0 items-center border-l border-healia-border-subtle px-3 text-healia-text-muted transition-colors hover:bg-healia-danger/[0.06] hover:text-healia-danger disabled:opacity-50 md:px-4"
                    >
                      <Trash2 className="h-4 w-4" strokeWidth={1.75} />
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </div>
    </V2Layout>
  );
}
