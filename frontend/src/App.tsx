import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  BrowserRouter,
  Navigate,
  Routes,
  Route,
  useLocation,
} from "react-router-dom";
import NotFound from "./pages/NotFound";
import HomePage from "@/v2/pages/HomePage";
import ConsultationRoutes from "@/v2/pages/consultation/ConsultationRoutes";
import AboutPage from "@/v2/pages/AboutPage";
import PrivacyPage from "@/v2/pages/PrivacyPage";
import LoginPage from "@/v2/pages/auth/LoginPage";
import SignupPage from "@/v2/pages/auth/SignupPage";
import ConsultationHistoryPage from "@/v2/pages/consultations/ConsultationHistoryPage";
import ConsultationDetailPage from "@/v2/pages/consultations/ConsultationDetailPage";
import { AuthProvider } from "@/v2/context/AuthContext";
import { ProtectedRoute } from "@/v2/components/auth/ProtectedRoute";

const queryClient = new QueryClient();

function StripV2Prefix() {
  const { pathname, search, hash } = useLocation();
  const stripped = pathname.replace(/^\/v2/, "") || "/";
  return <Navigate to={`${stripped}${search}${hash}`} replace />;
}

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route
              path="/consultations"
              element={
                <ProtectedRoute>
                  <ConsultationHistoryPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/consultations/:id"
              element={
                <ProtectedRoute>
                  <ConsultationDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/consultation/*"
              element={
                <ProtectedRoute>
                  <ConsultationRoutes />
                </ProtectedRoute>
              }
            />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/privacy" element={<PrivacyPage />} />

            <Route path="/v2" element={<Navigate to="/" replace />} />
            <Route path="/v2/*" element={<StripV2Prefix />} />

            <Route
              path="/conversation"
              element={<Navigate to="/consultation" replace />}
            />
            <Route
              path="/conversation/chat"
              element={<Navigate to="/consultation" replace />}
            />
            <Route
              path="/live-voice"
              element={<Navigate to="/consultation" replace />}
            />
            <Route path="/features" element={<Navigate to="/" replace />} />

            <Route path="*" element={<NotFound />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
