import { Route, Routes } from "react-router-dom";
import { ConsultationProvider } from "@/v2/context/ConsultationContext";
import { LiveKitConsultationShell } from "@/v2/components/consultation/LiveKitConsultationShell";
import StartConsultationPage from "@/v2/pages/consultation/StartConsultationPage";
import SessionPage from "@/v2/pages/consultation/SessionPage";
import ProcessingPage from "@/v2/pages/consultation/ProcessingPage";
import ResultsPage from "@/v2/pages/consultation/ResultsPage";

export default function ConsultationRoutes() {
  return (
    <ConsultationProvider>
      <LiveKitConsultationShell>
        <Routes>
          <Route index element={<StartConsultationPage />} />
          <Route path="session" element={<SessionPage />} />
          <Route path="processing" element={<ProcessingPage />} />
          <Route path="results" element={<ResultsPage />} />
        </Routes>
      </LiveKitConsultationShell>
    </ConsultationProvider>
  );
}
