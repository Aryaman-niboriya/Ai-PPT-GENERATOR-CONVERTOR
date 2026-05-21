import "./index.css";

import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster as HotToaster } from "react-hot-toast";
import { GoogleOAuthProvider } from "@react-oauth/google";


// Pages
import Index from "./pages/Index";
import Dashboard from "./pages/Dashboard";
import GeneratePPT from "./pages/GeneratePPT";
import ConvertPPT from "./pages/ConvertPPT";
import Features from "./pages/Features";
import About from "./pages/About";
import NotFound from "./pages/NotFound";
import Activity from "./pages/Activity";
import Analytics from "./pages/Analytics";
import Templates from "./pages/Templates";

// Components
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import FloatingHelpButton from "./components/FloatingHelpButton";
import Chatbot from './components/ui/Chatbot';
import ProtectedRoute from "./components/ProtectedRoute";

// Contexts
import { AuthProvider } from "./contexts/AuthContext";
import { ThemeProvider } from "./contexts/ThemeContext";

const queryClient = new QueryClient();

// ProtectedLayout: Navbar, Footer, etc. sirf jab user authenticated ho
import { useAuth } from "./contexts/AuthContext";

const ProtectedLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return null;
  if (!isAuthenticated) return null;
  return <>{children}</>;
};

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";

const App = () => (
  <GoogleOAuthProvider clientId={googleClientId}>
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <ThemeProvider>
          <AuthProvider>
            <BrowserRouter>
              <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 transition-colors duration-300">
                <Navbar />
                <main className="relative">
                  <Routes>
                    <Route path="/" element={<Index />} />
                    <Route path="/dashboard" element={<ProtectedRoute><ProtectedLayout><Dashboard /></ProtectedLayout></ProtectedRoute>} />
                    <Route path="/generate" element={<ProtectedRoute><ProtectedLayout><GeneratePPT /></ProtectedLayout></ProtectedRoute>} />
                    <Route path="/convert" element={<ProtectedRoute><ProtectedLayout><ConvertPPT /></ProtectedLayout></ProtectedRoute>} />
                    <Route path="/activity" element={<ProtectedRoute><ProtectedLayout><Activity /></ProtectedLayout></ProtectedRoute>} />
                    <Route path="/analytics" element={<ProtectedRoute><ProtectedLayout><Analytics /></ProtectedLayout></ProtectedRoute>} />
                    <Route path="/templates" element={<ProtectedRoute><ProtectedLayout><Templates /></ProtectedLayout></ProtectedRoute>} />
                    <Route path="/features" element={<Features />} />
                    <Route path="/about" element={<About />} />
                    <Route path="*" element={<NotFound />} />
                  </Routes>
                </main>
                <ProtectedLayout>
                <Footer />
                <FloatingHelpButton />
                  <ProtectedRoute><Chatbot /></ProtectedRoute>
                </ProtectedLayout>
              </div>
              <HotToaster
                position="top-right"
                toastOptions={{
                  duration: 4000,
                  style: {
                    background: "#1f2937",
                    color: "#f9fafb",
                    borderRadius: "12px",
                    boxShadow:
                      "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)",
                  },
                }}
              />
            </BrowserRouter>
          </AuthProvider>
        </ThemeProvider>
        <Toaster />
        <Sonner />
      </TooltipProvider>
    </QueryClientProvider>
  </GoogleOAuthProvider>
);

export default App;
