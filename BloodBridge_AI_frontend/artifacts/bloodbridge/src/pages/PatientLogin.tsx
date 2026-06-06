import { useState } from "react";
import { ThemeToggle } from "@/components/ThemeToggle";

import { Link, useLocation } from "wouter";
import { ChevronRight, ShieldCheck, Calendar, Activity, Users } from "lucide-react";
import { Input } from "@/components/ui/input";
import { login } from "@/lib/api";

export default function PatientLogin() {
  const [, setLocation] = useLocation();
  const [isLoading, setIsLoading] = useState(false);

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      const res = await login(identifier, password, "patient");
      localStorage.setItem("auth_token", res.access_token);
      localStorage.setItem("patient_id", res.user.patient_id);
      setLocation(`/patient?id=${res.user.patient_id}`);
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 dark:from-[#030712] dark:to-[#0F1929] text-slate-800 dark:text-slate-200 font-sans pb-20 relative selection:bg-teal-500/30">
      <div className="absolute top-4 right-4 z-50"><ThemeToggle /></div>
      {/* Sticky header */}
      <nav className="sticky top-0 w-full z-50 bg-white/80 dark:bg-[#030712]/80 backdrop-blur-md border-b border-slate-200 dark:border-white/5 px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 bg-teal-600 rounded-tl-full rounded-tr-full rounded-bl-full rounded-br-none rotate-45 flex items-center justify-center">
            <div className="w-1 h-1 bg-white dark:bg-slate-950 rounded-full -rotate-45" />
          </div>
          <span className="font-serif font-bold text-slate-900 dark:text-white">inquilab AI</span>
        </div>
        <Link href="/" className="text-xs text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors">
          ← Back to home
        </Link>
      </nav>

      <div className="max-w-md mx-auto px-4 pt-12 space-y-8">
        {/* Hero block */}
        <div className="text-center space-y-4">
          <div className="w-16 h-16 mx-auto bg-teal-500/10 rounded-full flex items-center justify-center border border-teal-500/20">
            <ShieldCheck className="w-8 h-8 text-teal-500 dark:text-teal-400" />
          </div>
          <h1 className="text-3xl font-serif font-bold text-slate-900 dark:text-white">Patient Portal</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 max-w-[280px] mx-auto leading-relaxed">
            Access your care dashboard, transfusion history & donor network
          </p>
        </div>

        {/* Login card */}
        <div className="bg-white/80 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 backdrop-blur-sm shadow-xl">
          <form onSubmit={handleLogin} className="space-y-4">
            {error && (
              <div className="p-3 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-500/10 rounded-md border border-red-200 dark:border-red-500/30">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-600 dark:text-slate-300">Patient ID or Phone</label>
              <Input 
                required 
                placeholder="P-10234 or +91..." 
                className="bg-slate-50 dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 h-11"
                value={identifier}
                onChange={e => setIdentifier(e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-600 dark:text-slate-300">Password</label>
              <Input 
                type="password" 
                required 
                className="bg-slate-50 dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white h-11"
                value={password}
                onChange={e => setPassword(e.target.value)}
              />
            </div>

            <button 
              type="submit" 
              disabled={isLoading}
              className="w-full bg-red-600 hover:bg-red-700 text-white rounded-xl py-3 font-semibold flex items-center justify-center gap-2 transition-colors mt-2"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>Access My Dashboard <ChevronRight className="w-4 h-4" /></>
              )}
            </button>
            
            <p className="text-[10px] text-slate-500 dark:text-slate-400 text-center leading-relaxed pt-2">
              Your data is encrypted and protected. Hospital staff only have access to your treatment records.
            </p>
          </form>
          
          <div className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
            Don't have an account?{" "}
            <Link href="/signup" className="text-teal-600 dark:text-teal-400 hover:text-teal-500 dark:hover:text-teal-300 font-medium">
              Sign up
            </Link>
          </div>
        </div>

        {/* Quick access tiles */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-3 text-center flex flex-col items-center gap-1.5">
            <div className="w-8 h-8 rounded-full bg-red-500/10 text-red-500 dark:text-red-400 flex items-center justify-center text-sm font-bold font-mono">B+</div>
            <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase tracking-wider">Blood Type</span>
          </div>
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-3 text-center flex flex-col items-center gap-1.5">
            <div className="w-8 h-8 rounded-full bg-teal-500/10 text-teal-500 dark:text-teal-400 flex items-center justify-center"><Calendar className="w-4 h-4" /></div>
            <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase tracking-wider">Next Tx</span>
          </div>
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-3 text-center flex flex-col items-center gap-1.5">
            <div className="w-8 h-8 rounded-full bg-amber-500/10 text-amber-500 dark:text-amber-400 flex items-center justify-center"><Activity className="w-4 h-4" /></div>
            <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase tracking-wider">Status</span>
          </div>
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-3 text-center flex flex-col items-center gap-1.5">
            <div className="w-8 h-8 rounded-full bg-blue-500/10 text-blue-500 dark:text-blue-400 flex items-center justify-center"><Users className="w-4 h-4" /></div>
            <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase tracking-wider">Donors</span>
          </div>
        </div>

        {/* Privacy note */}
        <div className="text-center">
          <span className="inline-flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-900/50 px-3 py-1.5 rounded-full border border-slate-200 dark:border-slate-800">
            🔒 Your data is visible only to your care team at KIMS Secunderabad
          </span>
        </div>
      </div>
    </div>
  );
}
