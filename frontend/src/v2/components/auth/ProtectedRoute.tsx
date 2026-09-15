import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/v2/context/AuthContext";
import { V2PageLoader } from "@/v2/components/V2Loader";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <V2PageLoader label="Checking your session…" />;
  }

  if (!isAuthenticated) {
    const next = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/login?next=${next}`} replace />;
  }

  return children;
}
