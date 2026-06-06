/**
 * DemandForecastPanel — A5 additive component for the Admin dashboard.
 * Renders the weekly blood-demand forecast (A3 agent) as a grouped bar chart +
 * AI summary card + shortage alert banners. Additive only.
 */
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid,
} from "recharts";
import { TrendingUp, AlertTriangle, RefreshCw, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { DemandForecast, getDemandForecast, runDemandForecast, triggerEmergency } from "@/lib/api";

const BLOOD_COLORS: Record<string, string> = {
  "O+": "#ef4444", "O-": "#b91c1c", "A+": "#3b82f6", "A-": "#1d4ed8",
  "B+": "#22c55e", "B-": "#15803d", "AB+": "#a855f7", "AB-": "#7e22ce",
};
const BLOOD_TYPES = Object.keys(BLOOD_COLORS);

function relativeTime(iso?: string): string {
  if (!iso) return "never";
  const then = new Date(iso).getTime();
  const diff = Date.now() - then;
  const h = Math.floor(diff / 3_600_000);
  if (h < 1) return "just now";
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export default function DemandForecastPanel() {
  const [forecast, setForecast] = useState<DemandForecast | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

  const load = () => {
    setLoading(true);
    getDemandForecast().then(setForecast).catch(() => setForecast(null)).finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, []);

  const handleRun = async () => {
    setRunning(true);
    try {
      await runDemandForecast();
      toast.success("Forecast running — refresh in a few seconds.");
      setTimeout(load, 4000);
    } catch { toast.error("Failed to trigger forecast."); }
    finally { setRunning(false); }
  };

  const startOutreach = async (bloodType: string) => {
    try {
      await triggerEmergency({ patient_id: "P-FORECAST", blood_type: bloodType, city: "Hyderabad", ward: "ICU", hospital: "Blood Warriors HQ" });
      toast.success(`Outreach started for ${bloodType}.`);
    } catch { toast.error("Failed to start outreach."); }
  };

  // Transform forecast_json → recharts rows
  const chartData = (forecast?.forecast_json || []).map((wk) => ({
    week: wk.week_label,
    ...wk.blood_type_counts,
  }));
  const supply = forecast?.supply_json || {};

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 mt-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-teal-400" /> Blood Demand Forecast — Next 28 Days
          </h3>
          {forecast?.generated_at && (
            <p className="text-[11px] text-slate-500 mt-0.5">Updated {relativeTime(forecast.generated_at)}</p>
          )}
        </div>
        <button onClick={handleRun} disabled={running}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold
                     bg-slate-800 text-slate-300 border border-slate-700 hover:bg-slate-700">
          {running ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />} Run Forecast
        </button>
      </div>

      {loading ? (
        <div className="space-y-3">
          <div className="h-24 bg-slate-800/50 rounded-xl animate-pulse" />
          <div className="h-64 bg-slate-800/50 rounded-xl animate-pulse" />
        </div>
      ) : !forecast || forecast.message ? (
        <div className="text-center py-10 text-slate-500 text-sm">
          {forecast?.message || "No forecast available yet."}
          <div className="mt-2"><button onClick={handleRun} className="text-teal-400 underline text-xs">Run the first forecast</button></div>
        </div>
      ) : (
        <>
          {/* AI summary card */}
          {forecast.ai_summary && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
              className="bg-slate-900/70 border-l-4 border-teal-500 rounded-r-xl p-4 mb-4">
              <div className="text-[11px] uppercase tracking-wider text-teal-400 font-bold mb-1">AI Summary</div>
              <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">{forecast.ai_summary}</p>
            </motion.div>
          )}

          {/* Shortage banners */}
          {(forecast.shortage_alerts || []).map((alert, i) => {
            const bt = BLOOD_TYPES.find((t) => alert.includes(t));
            return (
              <motion.div key={i} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }}
                className="flex items-center justify-between bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-2.5 mb-2">
                <div className="flex items-center gap-2 text-xs text-red-300">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0" /> {alert}
                </div>
                {bt && (
                  <button onClick={() => startOutreach(bt)}
                    className="text-[11px] font-bold px-3 py-1 rounded-lg bg-red-500/20 text-red-300 border border-red-500/40 hover:bg-red-500/30 flex-shrink-0">
                    Start Outreach
                  </button>
                )}
              </motion.div>
            );
          })}

          {/* Grouped bar chart */}
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}
            className="h-72 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="week" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8, fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                {BLOOD_TYPES.map((bt) => (
                  <Bar key={bt} dataKey={bt} fill={BLOOD_COLORS[bt]} radius={[2, 2, 0, 0]} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Supply snapshot */}
          {Object.keys(supply).length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              <span className="text-[11px] text-slate-500 mr-1">Eligible supply now:</span>
              {Object.entries(supply).map(([bt, n]) => (
                <span key={bt} className="text-[11px] px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300">
                  {bt}: <b>{n as number}</b>
                </span>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
