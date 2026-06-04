import { useState } from "react";
import { Link, useLocation } from "wouter";
import { ChevronRight, ShieldCheck, Calendar, Activity, Users } from "lucide-react";
import { Input } from "@/components/ui/input";

export default function PatientLogin() {
  const [, setLocation] = useLocation();
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => {
      setLocation("/patient");
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#030712] to-[#0F1929] text-slate-200 font-sans pb-20 relative selection:bg-teal-500/30">
      {/* Sticky header */}
      <nav className="sticky top-0 w-full z-50 bg-[#030712]/80 backdrop-blur-md border-b border-white/5 px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 bg-teal-600 rounded-tl-full rounded-tr-full rounded-bl-full rounded-br-none rotate-45 flex items-center justify-center">
            <div className="w-1 h-1 bg-white rounded-full -rotate-45" />
          </div>
          <span className="font-serif font-bold text-white">BloodBridge AI</span>
        </div>
        <Link href="/" className="text-xs text-slate-400 hover:text-white transition-colors">
          ← Back to home
        </Link>
      </nav>

      <div className="max-w-md mx-auto px-4 pt-12 space-y-8">
        {/* Hero block */}
        <div className="text-center space-y-4">
          <div className="w-16 h-16 mx-auto bg-teal-500/10 rounded-full flex items-center justify-center border border-teal-500/20">
            <ShieldCheck className="w-8 h-8 text-teal-400" />
          </div>
          <h1 className="text-3xl font-serif font-bold text-white">Patient Portal</h1>
          <p className="text-sm text-slate-400 max-w-[280px] mx-auto leading-relaxed">
            Access your care dashboard, transfusion history & donor network
          </p>
        </div>

        {/* Login card */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm shadow-xl">
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-300">Patient ID</label>
              <Input 
                required 
                placeholder="P-10234" 
                defaultValue="P-10234"
                className="bg-slate-800 border-slate-700 text-white placeholder:text-slate-500 h-11"
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-300">Date of Birth</label>
              <Input 
                type="date" 
                required 
                defaultValue="2018-03-14"
                className="bg-slate-800 border-slate-700 text-white h-11 [color-scheme:dark]"
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
            
            <p className="text-[10px] text-slate-500 text-center leading-relaxed pt-2">
              Your data is encrypted and protected. Hospital staff only have access to your treatment records.
            </p>
          </form>
        </div>

        {/* Quick access tiles */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 text-center flex flex-col items-center gap-1.5">
            <div className="w-8 h-8 rounded-full bg-red-500/10 text-red-400 flex items-center justify-center text-sm font-bold font-mono">B+</div>
            <span className="text-[10px] text-slate-500 uppercase tracking-wider">Blood Type</span>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 text-center flex flex-col items-center gap-1.5">
            <div className="w-8 h-8 rounded-full bg-teal-500/10 text-teal-400 flex items-center justify-center"><Calendar className="w-4 h-4" /></div>
            <span className="text-[10px] text-slate-500 uppercase tracking-wider">Next Tx</span>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 text-center flex flex-col items-center gap-1.5">
            <div className="w-8 h-8 rounded-full bg-amber-500/10 text-amber-400 flex items-center justify-center"><Activity className="w-4 h-4" /></div>
            <span className="text-[10px] text-slate-500 uppercase tracking-wider">Status</span>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 text-center flex flex-col items-center gap-1.5">
            <div className="w-8 h-8 rounded-full bg-blue-500/10 text-blue-400 flex items-center justify-center"><Users className="w-4 h-4" /></div>
            <span className="text-[10px] text-slate-500 uppercase tracking-wider">Donors</span>
          </div>
        </div>

        {/* Privacy note */}
        <div className="text-center">
          <span className="inline-flex items-center gap-1.5 text-xs text-slate-500 bg-slate-900/50 px-3 py-1.5 rounded-full border border-slate-800">
            🔒 Your data is visible only to your care team at KIMS Secunderabad
          </span>
        </div>
      </div>
    </div>
  );
}