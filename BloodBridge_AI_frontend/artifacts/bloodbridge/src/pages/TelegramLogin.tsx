import { useEffect, useState } from "react";
import { useLocation } from "wouter";
import { telegramLogin } from "@/lib/api";
import { Loader2, CheckCircle, AlertCircle } from "lucide-react";
import { SiTelegram } from "react-icons/si";

export default function TelegramLogin() {
  const [, setLocation] = useLocation();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [error, setError] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");

    if (!token) {
      setStatus("error");
      setError("No token provided. Please use the link from Telegram.");
      return;
    }

    telegramLogin(token)
      .then((result) => {
        localStorage.setItem("auth_token", result.access_token);
        localStorage.setItem("donor_id", result.donor_id);
        setStatus("success");
        setTimeout(() => setLocation("/donor"), 1500);
      })
      .catch((err) => {
        setStatus("error");
        setError(err.message || "Login failed. Token may have expired.");
      });
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center px-4">
      <div className="bg-slate-800 border border-slate-700 rounded-2xl p-8 max-w-sm w-full text-center">
        <div className="w-16 h-16 mx-auto mb-6 bg-[#229ED9]/20 rounded-full flex items-center justify-center">
          <SiTelegram className="w-8 h-8 text-[#229ED9]" />
        </div>

        {status === "loading" && (
          <>
            <Loader2 className="w-8 h-8 text-teal-400 animate-spin mx-auto mb-4" />
            <h2 className="text-lg font-bold text-white mb-2">Logging you in...</h2>
            <p className="text-sm text-slate-400">Verifying your Telegram identity</p>
          </>
        )}

        {status === "success" && (
          <>
            <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto mb-4" />
            <h2 className="text-lg font-bold text-white mb-2">Welcome back!</h2>
            <p className="text-sm text-slate-400">Redirecting to your donor portal...</p>
          </>
        )}

        {status === "error" && (
          <>
            <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-4" />
            <h2 className="text-lg font-bold text-white mb-2">Login Failed</h2>
            <p className="text-sm text-red-300">{error}</p>
            <a
              href="https://t.me/ummedrakho_bot"
              className="mt-4 inline-block text-sm text-[#229ED9] hover:underline"
            >
              ← Back to Telegram Bot
            </a>
          </>
        )}
      </div>
    </div>
  );
}
