import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AudioProvider } from "@/context/AudioContext";
import VoiceInputPage from "@/pages/VoiceInputPage";
import ChatPage from "@/pages/ChatPage";
import Index from "./pages/Index";
import Conversation from "./pages/Conversation";
import StartConsultation from "./pages/StartConsultation";
import Features from "./pages/Features";
import About from "./pages/About";
import NotFound from "./pages/NotFound";
import LiveVoicePage from "./pages/LiveVoicePage";
import HomePage from "@/v2/pages/HomePage";
import { PlaceholderPage } from "@/v2/pages/PlaceholderPage";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <AudioProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
            <Route path="/conversation" element={<VoiceInputPage />} />
            <Route path="/conversation/chat" element={<ChatPage />} />
          <Route path="/consultation" element={<StartConsultation />} />
          <Route path="/live-voice" element={<LiveVoicePage />} />
          <Route path="/features" element={<Features />} />
          <Route path="/about" element={<About />} />
          <Route path="/v2" element={<HomePage />} />
          <Route
            path="/v2/consultation"
            element={
              <PlaceholderPage
                title="Start Consultation"
                description="The consultation flow is coming next. This page will prepare you before starting a voice health assessment."
              />
            }
          />
          <Route
            path="/v2/about"
            element={
              <PlaceholderPage
                title="About Healia"
                description="Learn about what Healia is, its limitations, and how it helps you understand your health."
              />
            }
          />
          <Route
            path="/v2/privacy"
            element={
              <PlaceholderPage
                title="Privacy"
                description="Information about how Healia handles your data and protects your privacy."
              />
            }
          />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
      </AudioProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
