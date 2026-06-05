import { useState } from "react";
import { Link, useLocation } from "wouter";
import { Heart, Activity, Award, Shield, ArrowRight } from "lucide-react";
import { Input } from "@/components/ui/input";
import { SiTelegram } from "react-icons/si";
import { login } from "@/lib/api";

export default function DonorLogin() {
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
      const res = await login("donor", identifier, password);
      localStorage.setItem("auth_token", res.access_token);
      localStorage.setItem("donor_id", res.user.donor_id);
      setLocation("/donor");
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#030712] to-[#0A1020] text-slate-200 font-sans pb-20 relative selection:bg-red-500/30">
      {/* Sticky header */}
      <nav className="sticky top-0 w-full z-50 bg-[#030712]/80 backdrop-blur-md border-b border-white/5 px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 bg-[#C8102E] rounded-tl-full rounded-tr-full rounded-bl-full rounded-br-none rotate-45 flex items-center justify-center">
            <div className="w-1 h-1 bg-white rounded-full -rotate-45" />
          </div>
          <span className="font-serif font-bold text-white">BloodBridge AI</span>
        </div>
        <Link href="/" className="text-xs text-slate-400 hover:text-white transition-colors">
          ← Back to home
        </Link>
      </nav>

      {/* Impact banner */}
      <div className="bg-gradient-to-r from-red-900/80 to-red-800/60 border-b border-red-500/30 px-4 py-2.5 flex items-center justify-center gap-2 text-xs font-medium text-white shadow-lg shadow-red-900/20">
        <div className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
        312 active heroes in your network
      </div>

      <div className="max-w-md mx-auto px-4 pt-10 space-y-8">
        {/* Hero block */}
        <div className="text-center space-y-4">
          <div className="w-16 h-16 mx-auto bg-red-500/10 rounded-full flex items-center justify-center border border-red-500/20">
            <Heart className="w-8 h-8 text-red-400 fill-red-400/20" />
          </div>
          <h1 className="text-3xl font-serif font-bold text-white tracking-tight">Welcome back, hero.</h1>
          <p className="text-sm text-slate-400 italic">
            "Every drop you give changes a life."
          </p>
        </div>

        {/* Login card */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <form onSubmit={handleLogin} className="space-y-4">
            {error && (
              <div className="p-3 text-sm text-red-400 bg-red-500/10 rounded-md border border-red-500/30">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-300">Donor ID or Phone</label>
              <Input 
                required 
                placeholder="D-10234 or +919000000000" 
                className="bg-slate-800 border-slate-700 text-white placeholder:text-slate-500 h-11"
                value={identifier}
                onChange={e => setIdentifier(e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-300">Password</label>
              <Input 
                type="password" 
                required 
                className="bg-slate-800 border-slate-700 text-white h-11"
                value={password}
                onChange={e => setPassword(e.target.value)}
              />
            </div>

            <button 
              type="submit" 
              disabled={isLoading}
              className="w-full bg-[#C8102E] hover:bg-[#A00D24] text-white rounded-xl py-3 font-semibold flex items-center justify-center gap-2 transition-colors mt-2"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>Enter Donor Portal <ArrowRight className="w-4 h-4" /></>
              )}
            </button>
            
            <div className="flex items-center justify-center gap-2 pt-3">
              <SiTelegram className="w-4 h-4 text-[#229ED9]" />
              <p className="text-xs text-slate-500">
                You can also log in via Telegram: <a href="#" className="text-[#229ED9] hover:underline">@BloodBridgeBot</a>
              </p>
            </div>
          </form>
          
          <div className="mt-6 text-center text-sm text-slate-400">
            Don't have an account?{" "}
            <Link href="/signup" className="text-red-400 hover:text-red-300 font-medium">
              Sign up
            </Link>
          </div>
        </div>

        {/* Quick stats */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3 text-center">
            <div className="text-lg font-bold text-red-400 font-mono">13</div>
            <div className="text-[10px] text-slate-500 uppercase">Lives Saved</div>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3 text-center">
            <div className="text-lg font-bold text-teal-400 font-mono">13</div>
            <div className="text-[10px] text-slate-500 uppercase">Donations</div>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3 text-center">
            <div className="text-lg font-bold text-amber-400 font-mono">#2</div>
            <div className="text-[10px] text-slate-500 uppercase">City Rank</div>
          </div>
        </div>

        {/* Badges preview */}
        <div className="flex justify-center gap-2">
          <div className="px-3 py-1 bg-amber-500/10 border border-amber-500/30 text-amber-400 rounded-full text-xs font-medium shadow-[0_0_10px_rgba(245,158,11,0.1)]">
            Blood Hero
          </div>
          <div className="px-3 py-1 bg-teal-500/10 border border-teal-500/30 text-teal-400 rounded-full text-xs font-medium shadow-[0_0_10px_rgba(20,241,217,0.1)]">
            Life Saver
          </div>
          <div className="px-3 py-1 bg-red-500/10 border border-red-500/30 text-red-400 rounded-full text-xs font-medium shadow-[0_0_10px_rgba(239,68,68,0.1)]">
            Crisis Hero
          </div>
        </div>

        {/* Patient link */}
        <div className="bg-red-950/20 border border-red-900/50 rounded-xl p-4 text-center">
          <p className="text-sm text-slate-300 mb-3">
            Your next donation saves <span className="font-bold text-white">Aarav (7 yrs, B+)</span>.
          </p>
          <button className="text-xs bg-white/10 hover:bg-white/20 text-white px-4 py-1.5 rounded-lg transition-colors border border-white/5">
            View Request →
          </button>
        </div>

      </div>
    </div>
  );
}