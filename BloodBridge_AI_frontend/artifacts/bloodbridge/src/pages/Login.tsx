import { useState } from "react";
import { Link, useLocation } from "wouter";
import { Loader2, Eye, EyeOff } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { login } from "@/lib/api";

export default function Login() {
  const [, setLocation] = useLocation();
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      const res = await login(email, password, "staff");
      localStorage.setItem("auth_token", res.access_token);
      localStorage.setItem("staff_id", res.user.staff_id);
      setLocation("/dashboard/emergency");
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-white font-sans">
      {/* Left panel - Branding */}
      <div className="hidden md:flex flex-col flex-1 bg-slate-800 text-white p-12 relative overflow-hidden">
        <div className="relative z-10 flex flex-col h-full">
          <div className="flex items-center gap-3 mb-auto">
            <div className="w-8 h-8 bg-teal-600 rounded-tl-full rounded-tr-full rounded-bl-full rounded-br-none rotate-45 flex items-center justify-center">
              <div className="w-2 h-2 bg-white rounded-full -rotate-45" />
            </div>
            <span className="font-serif font-bold text-2xl">BloodBridge <span className="text-teal-400">AI</span></span>
          </div>

          <div className="mt-auto">
            <h1 className="text-4xl font-light mb-4">Coordinate <br/><span className="font-bold">life-saving blood chains</span></h1>
            <p className="text-slate-400 mb-8 max-w-md">Access the AI-powered emergency operations center to oversee active requests, manage donor matching, and monitor system health.</p>
            
            <div className="flex gap-2 flex-wrap mb-12">
              <span className="px-3 py-1 bg-slate-700/50 rounded-full text-xs text-slate-300 font-mono">LangGraph</span>
              <span className="px-3 py-1 bg-slate-700/50 rounded-full text-xs text-slate-300 font-mono">Neo4j Aura</span>
              <span className="px-3 py-1 bg-slate-700/50 rounded-full text-xs text-slate-300 font-mono">Telegram API</span>
            </div>

            {/* Live Status Panel */}
            <div className="bg-slate-900/50 border border-slate-700 rounded-xl p-4 w-72">
              <div className="text-xs text-slate-400 uppercase tracking-wider mb-3">Live Systems</div>
              <div className="space-y-3">
                {["Core API", "Matching Engine", "Comm Gateway", "Graph DB"].map(sys => (
                  <div key={sys} className="flex justify-between items-center text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                      <span className="text-slate-200">{sys}</span>
                    </div>
                    <span className="font-mono text-xs text-teal-400">{Math.floor(Math.random() * 50 + 20)}ms</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right panel - Form */}
      <div className="flex-1 flex flex-col justify-center items-center p-8">
        <div className="w-full max-w-sm">
          <div className="md:hidden flex items-center gap-3 mb-12 justify-center">
            <div className="w-8 h-8 bg-teal-600 rounded-tl-full rounded-tr-full rounded-bl-full rounded-br-none rotate-45 flex items-center justify-center">
              <div className="w-2 h-2 bg-white rounded-full -rotate-45" />
            </div>
            <span className="font-serif font-bold text-2xl text-slate-800">BloodBridge</span>
          </div>

          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-slate-900 mb-2">Staff Login</h2>
            <p className="text-slate-500 text-sm">Enter your hospital credentials to access the OC.</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            {error && (
              <div className="p-3 text-sm text-red-500 bg-red-50 rounded-md border border-red-100">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="email">Work Email</Label>
              <Input 
                id="email" 
                type="email" 
                placeholder="dr.name@hospital.org" 
                required 
                className="bg-slate-50" 
                value={email}
                onChange={e => setEmail(e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between">
                <Label htmlFor="password">Password</Label>
                <a href="#" className="text-xs text-teal-600 hover:text-teal-700">Forgot password?</a>
              </div>
              <div className="relative">
                <Input 
                  id="password" 
                  type={showPassword ? "text" : "password"} 
                  required 
                  className="bg-slate-50 pr-10" 
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                />
                <button 
                  type="button" 
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button 
              type="submit" 
              disabled={isLoading}
              className="w-full bg-teal-600 hover:bg-teal-700 text-white rounded-lg py-2.5 font-medium transition-colors mt-6 flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Authenticating...</>
              ) : (
                "Sign in as Hospital Staff →"
              )}
            </button>
          </form>
          
          <div className="mt-6 text-center text-sm text-slate-500">
            Don't have an account?{" "}
            <Link href="/signup" className="text-teal-600 hover:text-teal-700 font-medium">
              Sign up
            </Link>
          </div>
          
          <div className="mt-8 text-center text-xs text-slate-400">
            Secure access provided by BloodBridge HQ.
          </div>
        </div>
      </div>
    </div>
  );
}
