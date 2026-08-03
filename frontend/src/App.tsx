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
          <Route path="/features" element={<Features />} />
          <Route path="/about" element={<About />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
      </AudioProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
