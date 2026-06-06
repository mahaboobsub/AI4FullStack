import { useState } from "react";
import { ThemeToggle } from "@/components/ThemeToggle";

import { Link, useLocation } from "wouter";
import { Loader2, Eye, EyeOff, UserPlus, Upload, CheckCircle } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { signup, uploadBloodCard } from "@/lib/api";

export default function SignUp() {
  const [, setLocation] = useLocation();
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [role, setRole] = useState<"donor" | "patient" | "staff">("donor");
  const [ocrLoading, setOcrLoading] = useState(false);
  const [ocrResult, setOcrResult] = useState<{ blood_group: string | null; name: string | null } | null>(null);

  const handleCardUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setOcrLoading(true);
    setOcrResult(null);
    try {
      const result = await uploadBloodCard(file);
      setOcrResult(result);
      // Auto-fill the blood group select if detected
      if (result.blood_group) {
        const select = document.getElementById("bloodGroup") as HTMLSelectElement;
        if (select) select.value = result.blood_group;
      }
      // Auto-fill first name if detected
      if (result.name) {
        const firstName = document.getElementById("firstName") as HTMLInputElement;
        if (firstName && !firstName.value) firstName.value = result.name.split(" ")[0];
        const lastName = document.getElementById("lastName") as HTMLInputElement;
        if (lastName && !lastName.value && result.name.split(" ").length > 1) lastName.value = result.name.split(" ").slice(1).join(" ");
      }
    } catch {
      setOcrResult(null);
    } finally {
      setOcrLoading(false);
    }
  };

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    const fd = new FormData(e.currentTarget as HTMLFormElement);
    const payload = {
      role,
      first_name: fd.get("firstName") as string,
      last_name: fd.get("lastName") as string,
      password: fd.get("password") as string,
      email: fd.get("email") as string | undefined,
      phone: fd.get("phone") as string | undefined,
      blood_group: fd.get("bloodGroup") as string | undefined,
    };
    try {
      await signup(payload);
      if (role === "donor") {
        setLocation("/donor/login");
      } else if (role === "patient") {
        setLocation("/patient/login");
      } else {
        setLocation("/login");
      }
    } catch(err: any) {
      alert(err.message || "Failed to sign up");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-900 font-sans selection:bg-teal-500/30">
      <div className="absolute top-4 right-4 z-50"><ThemeToggle /></div>
      {/* Left panel - Branding */}
      <div className="hidden md:flex flex-col flex-1 bg-slate-800 text-white p-12 relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(20,241,217,0.05),transparent)]" />
        <div className="relative z-10 flex flex-col h-full">
          <div className="flex items-center gap-3 mb-auto">
            <div className="w-8 h-8 bg-teal-600 rounded-tl-full rounded-tr-full rounded-bl-full rounded-br-none rotate-45 flex items-center justify-center">
              <div className="w-2 h-2 bg-white dark:bg-slate-950 rounded-full -rotate-45" />
            </div>
            <span className="font-serif font-bold text-2xl">inquilab <span className="text-teal-400">AI</span></span>
          </div>

          <div className="mt-auto">
            <h1 className="text-4xl font-light mb-4">Join the <br/><span className="font-bold">life-saving network</span></h1>
            <p className="text-slate-400 mb-8 max-w-md">Whether you are registering as a donor, a patient in need, or hospital staff, your account connects you to our AI-powered emergency operations.</p>
            
            <div className="flex gap-2 flex-wrap mb-12">
              <span className="px-3 py-1 bg-slate-700/50 rounded-full text-xs text-slate-300 font-mono">1L+ Patients</span>
              <span className="px-3 py-1 bg-slate-700/50 rounded-full text-xs text-slate-300 font-mono">14 AI Agents</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right panel - Form */}
      <div className="flex-1 flex flex-col justify-center items-center p-8 bg-white dark:bg-slate-950 relative">
        <div className="w-full max-w-md">
          <div className="md:hidden flex items-center gap-3 mb-8 justify-center">
            <div className="w-8 h-8 bg-teal-600 rounded-tl-full rounded-tr-full rounded-bl-full rounded-br-none rotate-45 flex items-center justify-center">
              <div className="w-2 h-2 bg-white dark:bg-slate-950 rounded-full -rotate-45" />
            </div>
            <span className="font-serif font-bold text-2xl text-slate-800 dark:text-slate-200">inquilab AI</span>
          </div>

          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">Create an Account</h2>
            <p className="text-slate-500 dark:text-slate-400 text-sm">Select your role to join the platform.</p>
          </div>

          <div className="flex gap-2 mb-8 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
            {["donor", "patient", "staff"].map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => setRole(r as any)}
                className={`flex-1 py-2 text-sm font-medium rounded-md capitalize transition-colors ${role === r ? 'bg-white dark:bg-slate-950 shadow-sm text-teal-700' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700'}`}
              >
                {r}
              </button>
            ))}
          </div>

          <form onSubmit={handleSignUp} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="firstName">First Name</Label>
                <Input id="firstName" name="firstName" required className="bg-slate-50 dark:bg-slate-900 dark:border-slate-800 dark:text-slate-100" placeholder="John" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="lastName">Last Name</Label>
                <Input id="lastName" name="lastName" required className="bg-slate-50 dark:bg-slate-900 dark:border-slate-800 dark:text-slate-100" placeholder="Doe" />
              </div>
            </div>

            {role === "staff" ? (
              <div className="space-y-2">
                <Label htmlFor="email">Work Email</Label>
                <Input id="email" name="email" type="email" required className="bg-slate-50 dark:bg-slate-900 dark:border-slate-800 dark:text-slate-100" placeholder="dr.name@hospital.org" />
              </div>
            ) : (
              <div className="space-y-2">
                <Label htmlFor="phone">Phone Number</Label>
                <Input id="phone" name="phone" type="tel" required className="bg-slate-50 dark:bg-slate-900 dark:border-slate-800 dark:text-slate-100" placeholder="9876543210" />
              </div>
            )}

            {role !== "staff" && (
              <div className="space-y-2">
                <Label htmlFor="bloodGroup">Blood Group</Label>
                <select id="bloodGroup" name="bloodGroup" required className="flex h-10 w-full rounded-md border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 dark:border-slate-800 dark:text-slate-100 px-3 py-2 text-sm ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2">
                  <option value="">Select...</option>
                  <option value="A+">A+</option>
                  <option value="A-">A-</option>
                  <option value="B+">B+</option>
                  <option value="B-">B-</option>
                  <option value="AB+">AB+</option>
                  <option value="AB-">AB-</option>
                  <option value="O+">O+</option>
                  <option value="O-">O-</option>
                </select>
              </div>
            )}

            {/* Blood Card OCR Upload — donor only */}
            {role === "donor" && (
              <div className="space-y-2">
                <Label>Upload Blood Card (Optional)</Label>
                <div className="border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-lg p-4 text-center hover:border-teal-500/50 transition-colors">
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    id="bloodCardFile"
                    onChange={handleCardUpload}
                  />
                  <label htmlFor="bloodCardFile" className="cursor-pointer flex flex-col items-center gap-2">
                    {ocrLoading ? (
                      <Loader2 className="w-6 h-6 text-teal-500 animate-spin" />
                    ) : ocrResult?.blood_group ? (
                      <CheckCircle className="w-6 h-6 text-emerald-500" />
                    ) : (
                      <Upload className="w-6 h-6 text-slate-400" />
                    )}
                    <span className="text-xs text-slate-500 dark:text-slate-400">
                      {ocrLoading ? "Scanning with AWS Textract..." : ocrResult?.blood_group ? `Detected: ${ocrResult.blood_group}${ocrResult.name ? ` • ${ocrResult.name}` : ''}` : "Upload blood donation card to auto-fill"}
                    </span>
                  </label>
                  {/* Show detected antigens */}
                  {ocrResult?.antigen_panel && Object.keys(ocrResult.antigen_panel).length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5 justify-center">
                      {Object.entries(ocrResult.antigen_panel).map(([ag, val]) => (
                        <span key={ag} className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${val === 'Positive' ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-400 dark:border-emerald-800' : 'bg-red-50 text-red-600 border-red-200 dark:bg-red-950/30 dark:text-red-400 dark:border-red-800'}`}>
                          {ag}: {val === 'Positive' ? '+' : '−'}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
            
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input 
                  id="password" 
                  name="password"
                  type={showPassword ? "text" : "password"} 
                  required 
                  className="bg-slate-50 dark:bg-slate-900 dark:border-slate-800 dark:text-slate-100 pr-10" 
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
                <><Loader2 className="w-4 h-4 animate-spin" /> Creating account...</>
              ) : (
                <><UserPlus className="w-4 h-4" /> Sign Up</>
              )}
            </button>
          </form>
          
          <div className="mt-8 text-center text-sm text-slate-500 dark:text-slate-400">
            Already have an account?{" "}
            <Link href={role === "donor" ? "/donor/login" : role === "patient" ? "/patient/login" : "/login"} className="text-teal-600 hover:text-teal-700 font-medium">
              Log in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
