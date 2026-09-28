import { MessageCircleWarning } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { ConsultationLayout } from "@/v2/components/consultation/ConsultationLayout";
import { V2Button } from "@/v2/components/V2Button";
import { useConsultation } from "@/v2/context/ConsultationContext";

export default function InsufficientInfoPage() {
  const navigate = useNavigate();
  const { startSession, resetConsultation } = useConsultation();

  const handleRestart = () => {
    resetConsultation();
    startSession();
    navigate("/consultation/session");
  };

  return (
    <ConsultationLayout>
      <div className="mx-auto flex min-h-[calc(100vh-3.5rem)] max-w-page flex-col items-center justify-center px-5 py-10">
        <div className="mx-auto w-full max-w-md rounded-xl border border-healia-border bg-healia-bg-secondary px-5 py-6 text-center">
          <span className="mx-auto flex h-11 w-11 items-center justify-center rounded-lg bg-healia-brand-light text-healia-brand">
            <MessageCircleWarning className="h-5 w-5" strokeWidth={1.75} />
          </span>

          <h1 className="mt-4 text-xl font-semibold tracking-tight text-healia-text">
            Not enough information yet
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-healia-text-secondary">
            Healia needs to hear about your symptoms before preparing guidance.
            This session ended before enough was shared.
          </p>

          <div className="mt-5 rounded-lg border border-healia-border bg-healia-bg px-3.5 py-3 text-left">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-healia-text-muted">
              What to do
            </p>
            <p className="mt-1.5 text-sm leading-relaxed text-healia-text-secondary">
              Start a new consultation and briefly describe what you&apos;re
              feeling. Healia will ask a few follow-ups, then prepare guidance.
            </p>
          </div>

          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <V2Button className="px-4 py-2 text-sm" onClick={handleRestart}>
              Start a new consultation
            </V2Button>
            <V2Button
              to="/"
              variant="secondary"
              className="px-4 py-2 text-sm"
            >
              Go home
            </V2Button>
          </div>
        </div>
      </div>
    </ConsultationLayout>
  );
}
