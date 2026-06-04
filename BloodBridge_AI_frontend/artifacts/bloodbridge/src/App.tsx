import { Switch, Route, Router as WouterRouter } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/lib/theme";
import NotFound from "@/pages/not-found";

import Landing from "@/pages/Landing";
import Login from "@/pages/Login";
import PatientLogin from "@/pages/PatientLogin";
import DonorLogin from "@/pages/DonorLogin";
import Emergency from "@/pages/dashboard/Emergency";
import Graph from "@/pages/dashboard/Graph";
import MapView from "@/pages/dashboard/Map";
import Donors from "@/pages/dashboard/Donors";
import Admin from "@/pages/dashboard/Admin";
import DonorPortal from "@/pages/DonorPortal";
import PatientDashboard from "@/pages/PatientDashboard";

const queryClient = new QueryClient();

function Router() {
  return (
    <Switch>
      <Route path="/" component={Landing} />
      <Route path="/login" component={Login} />
      <Route path="/patient/login" component={PatientLogin} />
      <Route path="/donor/login" component={DonorLogin} />
      <Route path="/dashboard/emergency" component={Emergency} />
      <Route path="/dashboard/graph" component={Graph} />
      <Route path="/dashboard/map" component={MapView} />
      <Route path="/dashboard/donors" component={Donors} />
      <Route path="/dashboard/admin" component={Admin} />
      <Route path="/donor" component={DonorPortal} />
      <Route path="/patient" component={PatientDashboard} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, "")}>
            <Router />
          </WouterRouter>
          <Toaster position="top-right" />
        </TooltipProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}

export default App;