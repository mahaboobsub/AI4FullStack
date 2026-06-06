/**
 * BloodBridgeCard — Feature 5
 * Shows the donor↔patient mapped pairs from bridge_memberships.
 * Used in both DonorPortal and PatientDashboard.
 */
import { useEffect, useState } from "react";
import { Heart, Loader2 } from "lucide-react";
import { getDonorBridges, getPatientBridges, type BridgeMember } from "@/lib/api";

interface Props {
  entityId: string;
  kind: "donor" | "patient";
}

export default function BloodBridgeCard({ entityId, kind }: Props) {
  const [members, setMembers] = useState<BridgeMember[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!entityId) return;
    setLoading(true);
    const fetcher = kind === "donor" ? getDonorBridges : getPatientBridges;
    fetcher(entityId)
      .then(setMembers)
      .catch(() => setMembers([]))
      .finally(() => setLoading(false));
  }, [entityId, kind]);

  if (loading) {
    return (
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5 flex justify-center py-8">
        <Loader2 className="w-5 h-5 animate-spin text-slate-500" />
      </div>
    );
  }

  if (members.length === 0) {
    return (
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 mb-2">
          <Heart className="w-3.5 h-3.5 text-red-400" /> Your Blood Bridge
        </h3>
        <p className="text-xs text-slate-500 italic text-center py-3">
          No bridge connections yet. Matches will appear here once linked.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5">
      <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 mb-4">
        <Heart className="w-3.5 h-3.5 text-red-400" /> Your Blood Bridge
      </h3>
      <div className="space-y-3">
        {members.map((m, i) => {
          const name = kind === "donor" ? m.patient_name : m.donor_name;
          const id = kind === "donor" ? m.patient_id : m.donor_id;
          const score = Math.round((m.antigen_score || 0.5) * 100);

          return (
            <div key={id || i} className="flex items-center gap-3 bg-slate-800/60 border border-slate-700 rounded-xl px-4 py-3">
              {/* Bridge connector dot */}
              <div className="flex flex-col items-center gap-0.5">
                <div className="w-2.5 h-2.5 rounded-full bg-red-500 shadow-[0_0_6px_rgba(239,68,68,0.4)]" />
                <div className="w-px h-6 bg-gradient-to-b from-red-500/60 to-teal-500/60" />
                <div className="w-2.5 h-2.5 rounded-full bg-teal-500 shadow-[0_0_6px_rgba(20,184,166,0.4)]" />
              </div>

              {/* Person info */}
              <div className="flex-1 min-w-0">
                <div className="text-sm font-semibold text-white truncate">{name || "Unknown"}</div>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-[10px] font-bold font-mono bg-slate-900 text-slate-300 px-1.5 py-0.5 rounded">
                    {m.blood_type}
                  </span>
                  <span className="text-[10px] text-slate-500">
                    {kind === "donor" ? "Patient" : "Donor"}
                  </span>
                </div>
              </div>

              {/* Antigen score */}
              <div className="text-right">
                <div className="text-sm font-mono font-bold text-teal-400">{score}%</div>
                <div className="text-[9px] text-slate-500 uppercase font-bold">Match</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
