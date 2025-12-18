import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import TemporalAnalysis from "./pages/TemporalAnalysis";
import GeospatialAnalysis from "./pages/GeospatialAnalysis";
import EconomicAnalysis from "./pages/EconomicAnalysis";
import MLPrediction from "./pages/MLPrediction";
import DataExplorer from "./pages/DataExplorer";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
    },
  },
});

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/temporal" element={<TemporalAnalysis />} />
          <Route path="/geospatial" element={<GeospatialAnalysis />} />
          <Route path="/economic" element={<EconomicAnalysis />} />
          <Route path="/ml" element={<MLPrediction />} />
          <Route path="/data" element={<DataExplorer />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
