import { useState } from "react";
import { optimizeAssignments, type OptimizeAssignmentsResult } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { GitBranch, Loader2 } from "lucide-react";
import { toast } from "sonner";

export default function AssignmentOptimizerPanel() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OptimizeAssignmentsResult | null>(null);

  const handleRun = async () => {
    setLoading(true);
    try {
      const data = await optimizeAssignments();
      setResult(data);
      const count = data.patient_count ?? Object.keys(data.assignments || {}).length;
      toast.success(count > 0 ? `Optimal plan for ${count} patient(s) computed.` : data.message);
    } catch {
      toast.error("Optimizer failed — check server logs or staff token.");
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const entries = Object.entries(result?.assignments || {});

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <GitBranch className="w-4 h-4" /> Hungarian Assignment Optimizer
        </CardTitle>
        <CardDescription>
          Read-only preview for concurrent IN_PROGRESS emergencies — no donors are auto-alerted.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Button
          onClick={handleRun}
          disabled={loading}
          className="bg-teal-600 hover:bg-teal-700 text-white gap-2"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <GitBranch className="w-4 h-4" />}
          Run Optimizer Preview
        </Button>

        {result && (
          <div className="text-sm text-muted-foreground border border-slate-200 dark:border-slate-800 rounded-lg p-3 bg-slate-50/50 dark:bg-slate-900/30">
            {result.message}
          </div>
        )}

        {entries.length > 0 && (
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {entries.map(([patientId, donors]) => (
              <div key={patientId} className="border border-slate-200 dark:border-slate-800 rounded-lg p-3">
                <div className="text-xs font-mono font-bold text-teal-600 dark:text-teal-400 mb-2">
                  {patientId} — {donors.length} donor(s)
                </div>
                <ul className="space-y-1">
                  {donors.map((d, i) => (
                    <li key={d.donor_id} className="text-xs flex justify-between gap-2">
                      <span className="font-medium truncate">{i + 1}. {d.name || d.donor_id}</span>
                      <span className="font-mono text-muted-foreground shrink-0">
                        score {d.match_score?.toFixed(2) ?? "—"} · {d.distance_km?.toFixed(1) ?? "—"} km
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
