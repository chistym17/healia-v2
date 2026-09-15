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
import { AudioProvider } from "@/context/AudioContext";
import NotFound from "./pages/NotFound";
import HomePage from "@/v2/pages/HomePage";
import ConsultationRoutes from "@/v2/pages/consultation/ConsultationRoutes";
import { PlaceholderPage } from "@/v2/pages/PlaceholderPage";

const queryClient = new QueryClient();

/** `/v2/...` → `/...` so old bookmarks still work. */
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
      <AudioProvider>
        <BrowserRouter>
          <Routes>
            {/* Primary (v2) routes */}
            <Route path="/" element={<HomePage />} />
            <Route path="/consultation/*" element={<ConsultationRoutes />} />
            <Route
              path="/about"
              element={
                <PlaceholderPage
                  title="About Healia"
                  description="Learn about what Healia is, its limitations, and how it helps you understand your health."
                />
              }
            />
            <Route
              path="/privacy"
              element={
                <PlaceholderPage
                  title="Privacy"
                  description="Information about how Healia handles your data and protects your privacy."
                />
              }
            />

            {/* Legacy /v2 URLs → canonical paths */}
            <Route path="/v2" element={<Navigate to="/" replace />} />
            <Route path="/v2/*" element={<StripV2Prefix />} />

            {/* Legacy v1 pages → v2 equivalents */}
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
        </BrowserRouter>
      </AudioProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
