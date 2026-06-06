// HealthStatusControl - M5 additive component.
// Lets a donor self-report being temporarily unavailable or available again.
// Calls POST /api/donors/{id}/health-status. Pure addition.
import { useState } from "react";
import { motion } from "framer-motion";
import { HeartPulse, Pause, Play, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { updateDonorHealthStatus } from "@/lib/api";

type HealthStatusControlProps = {
  donorId: string;
  initialAvailable?: boolean;
  onChange?: (available: boolean) => void;
};

export default function HealthStatusControl(props: HealthStatusControlProps) {
  const { donorId, initialAvailable = true, onChange } = props;
  const [available, setAvailable] = useState(initialAvailable);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [reason, setReason] = useState("");
  const [holdUntil, setHoldUntil] = useState("");
  const [pulse, setPulse] = useState(false);

  async function reportUnavailable() {
    if (!reason.trim()) {
      toast.error("Please add a short reason.");
      return;
    }
    setLoading(true);
    try {
      await updateDonorHealthStatus(donorId, {
        available: false,
        reason: reason.trim(),
        hold_until: holdUntil || undefined,
      });
      setAvailable(false);
      if (onChange) onChange(false);
      setShowForm(false);
      setReason("");
      setHoldUntil("");
      setPulse(true);
      setTimeout(() => setPulse(false), 400);
      toast.success("Thanks for letting us know. We have paused your requests and notified the team.");
    } catch {
      toast.error("Failed to update health status.");
    } finally {
      setLoading(false);
    }
  }

  async function markAvailable() {
    setLoading(true);
    try {
      await updateDonorHealthStatus(donorId, { available: true });
      setAvailable(true);
      if (onChange) onChange(true);
      setPulse(true);
      setTimeout(() => setPulse(false), 400);
      toast.success("Welcome back! You are active again.");
    } catch {
      toast.error("Failed to update health status.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <motion.div
      animate={pulse ? { scale: [1, 1.04, 1] } : {}}
      transition={{ duration: 0.3 }}
      className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5"
    >
      <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 mb-1">
        <HeartPulse className="w-3.5 h-3.5 text-rose-400" /> Health and Availability
      </h3>
      <p className="text-xs text-slate-400 mb-4">
        {available
          ? "You are active and may receive donation requests."
          : "You are paused. We will not send requests until you are back."}
      </p>

      {available && !showForm && (
        <button
          onClick={() => setShowForm(true)}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-sm font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30 hover:bg-amber-500/25"
        >
          <Pause className="w-4 h-4" /> Report Unavailable
        </button>
      )}

      {available && showForm && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className="space-y-2 bg-slate-800/40 border border-slate-700 rounded-xl p-3"
        >
          <input
            className="w-full bg-slate-900 border border-slate-700 text-white text-xs rounded px-2 py-1.5"
            placeholder="Reason (fever, hospitalized, recent checkup)"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
          <div>
            <label className="text-[11px] text-slate-400">Available again on (optional)</label>
            <input
              type="date"
              className="w-full bg-slate-900 border border-slate-700 text-white text-xs rounded px-2 py-1.5 mt-1"
              value={holdUntil}
              onChange={(e) => setHoldUntil(e.target.value)}
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={reportUnavailable}
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 hover:bg-amber-500/30"
            >
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Confirm Pause"}
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="px-3 py-1.5 rounded-lg text-xs text-slate-400 border border-slate-700 hover:bg-slate-800"
            >
              Cancel
            </button>
          </div>
        </motion.div>
      )}

      {!available && (
        <button
          onClick={markAvailable}
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-sm font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/25"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <span className="flex items-center gap-2"><Play className="w-4 h-4" /> I am Available Again</span>}
        </button>
      )}
    </motion.div>
  );
}
