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
      navigate("/v2/consultation");
    }
  }, [guidance, navigate]);

  if (!guidance) return null;

  const handleStartNew = () => {
    resetConsultation();
    navigate("/v2/consultation");
  };

  return (
    <ConsultationLayout>
      <div className="mx-auto max-w-content px-5 py-12 md:py-16 lg:px-0">
        <h1 className="text-2xl font-semibold text-healia-text md:text-3xl">
          Your health guidance
        </h1>

        <div className="mt-10">
          <GuidanceResults guidance={guidance} />
        </div>

        <p className="mt-10 text-sm text-healia-text-muted">
          Not medical advice or a diagnosis. For emergencies, call your local
          emergency number.
        </p>

        <div className="mt-8 flex flex-col gap-3 sm:flex-row">
          <V2Button to="/v2">Back to Home</V2Button>
          <V2Button variant="secondary" onClick={handleStartNew}>
            New consultation
          </V2Button>
        </div>
      </div>
    </ConsultationLayout>
  );
}
