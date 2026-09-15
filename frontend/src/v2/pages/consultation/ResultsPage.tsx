import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ConsultationLayout } from "@/v2/components/consultation/ConsultationLayout";
import { GuidanceResults } from "@/v2/components/consultation/GuidanceResults";
import { V2Button } from "@/v2/components/V2Button";
import { useConsultation } from "@/v2/context/ConsultationContext";

export default function ResultsPage() {
  const navigate = useNavigate();
  const { guidance, resetConsultation } = useConsultation();

  useEffect(() => {
    if (!guidance) {
      navigate("/consultation");
    }
  }, [guidance, navigate]);

  if (!guidance) return null;

  const handleStartNew = () => {
    resetConsultation();
    navigate("/consultation");
  };

  return (
    <ConsultationLayout>
      <div className="mx-auto flex h-[calc(100vh-3.5rem)] max-w-page flex-col px-5 py-5 md:px-8 md:py-6 lg:px-12">
        <div className="mb-5 flex flex-wrap items-end justify-between gap-3 border-b border-healia-border-subtle pb-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-widest text-healia-brand">
              Consultation complete
            </p>
            <h1 className="mt-1 text-xl font-semibold tracking-tight text-healia-text md:text-2xl">
              Your health guidance
            </h1>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <V2Button to="/" variant="secondary" className="px-4 py-2 text-sm">
              Back to Home
            </V2Button>
            <V2Button onClick={handleStartNew} className="px-4 py-2 text-sm">
              New consultation
            </V2Button>
          </div>
        </div>

        <GuidanceResults guidance={guidance} />

        <p className="mt-4 text-xs leading-relaxed text-healia-text-muted">
          Educational guidance only — not a medical diagnosis or treatment plan.
          For emergencies, call your local emergency number or seek urgent care
          now.
        </p>
      </div>
    </ConsultationLayout>
  );
}
