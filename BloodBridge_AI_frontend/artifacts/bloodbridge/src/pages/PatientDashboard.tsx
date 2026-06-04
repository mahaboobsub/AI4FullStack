import { useState, useEffect, lazy, Suspense } from "react";
import { AlertCircle, HeartPulse, Shield, Droplet, Calendar, Hospital, Activity } from "lucide-react";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { getPatientProfile, type PatientProfile } from "@/lib/api";
import CountUp from "react-countup";

const ForceGraph2D = lazy(() => import("react-force-graph-2d"));

export default function PatientDashboard() {
  const [profile, setProfile] = useState<PatientProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Read ?id= from URL, fallback to demo patient
    const params = new URLSearchParams(window.location.search);
    const patientId = params.get("id") || "P-10234";
    getPatientProfile(patientId)
      .then(setProfile)
      .catch((err) => setError(err?.message || "Failed to load patient profile"));
  }, []);

  if (error) return <div className="min-h-screen bg-[#030712] flex items-center justify-center text-red-400 font-mono text-sm px-8 text-center">Error: {error}</div>;
  if (!profile) return <div className="min-h-screen bg-[#030712] flex items-center justify-center text-slate-500 font-mono text-sm">Initializing Profile...</div>;

  const graphData = {
    nodes: [
      { id: profile.patient_id, name: "You", group: 1, val: 20 },
      ...profile.linked_donors.map(d => ({
        id: d.donor_id, name: d.donor_name, group: 2, val: 10,
        status: d.status, score: d.antigen_score
      }))
    ],
    links: profile.linked_donors.map(d => ({
      source: profile.patient_id, target: d.donor_id,
      score: d.antigen_score
    }))
  };

  // Calculate overdue days
  const dueDate = new Date(profile.next_transfusion_due);
  const today = new Date();
  const diffTime = today.getTime() - dueDate.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  const isOverdue = diffDays > 0;

  return (
    <div className="min-h-screen bg-[#030712] text-slate-200 font-sans pb-20 relative overflow-x-hidden selection:bg-red-500/30">
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(15,25,41,1),rgba(3,7,18,1))] z-[-1]" />
      
      <div className="max-w-md mx-auto px-4 pt-8 relative z-10 space-y-6">
        {/* Header */}
        <div className="flex justify-between items-start mb-2">
          <div>
            <h1 className="text-4xl font-serif font-bold text-white mb-2 tracking-tight">Hello, {profile.name.split(' ')[0]}</h1>
            <p className="text-sm text-slate-400 font-medium">Your care dashboard</p>
            <div className="flex items-center gap-1.5 mt-3 text-xs text-slate-500 bg-slate-900/50 w-fit px-2.5 py-1.5 rounded-md border border-slate-800">
              <Hospital className="w-3.5 h-3.5" /> 
              Managed by KIMS Secunderabad · Ward: {profile.ward}
            </div>
          </div>
          {profile.status === "CRITICAL" && (
            <div className="px-3 py-1.5 bg-red-500/10 text-red-400 border border-red-500/30 rounded-full text-[10px] font-black uppercase tracking-widest flex items-center gap-1.5 shadow-[0_0_15px_rgba(239,68,68,0.2)]">
              <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
              Critical
            </div>
          )}
        </div>

        {/* Vital Stats Grid */}
        <div className="grid grid-cols-2 gap-4">
          <div className={`bg-slate-900/80 border rounded-2xl p-4 backdrop-blur-sm relative overflow-hidden ${isOverdue ? 'border-red-900/50' : 'border-slate-800'}`}>
            {isOverdue && <div className="absolute inset-0 bg-red-500/5" />}
            <div className="relative z-10">
              <div className="text-xs text-slate-400 mb-2 flex items-center gap-1.5 uppercase font-bold tracking-wider"><Calendar className="w-3 h-3" /> Next Transfusion</div>
              <div className="text-lg font-bold text-white mb-1">
                {dueDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
              </div>
              {isOverdue ? (
                <div className="text-xs font-bold text-red-400 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" /> {diffDays} days overdue
                </div>
              ) : (
                <div className="text-xs text-emerald-400 font-medium">On track</div>
              )}
            </div>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 backdrop-blur-sm relative overflow-hidden flex flex-col items-center justify-center text-center">
            <div className="text-xs text-slate-400 mb-3 flex items-center gap-1.5 uppercase font-bold tracking-wider"><HeartPulse className="w-3 h-3 text-amber-400" /> Hemoglobin</div>
            
            {/* CSS Semicircle Gauge */}
            <div className="relative w-24 h-12 flex justify-center mt-2">
              <div className="absolute bottom-0 w-24 h-12 border-[8px] border-slate-800 rounded-t-full border-b-0" />
              <div 
                className="absolute bottom-0 w-24 h-12 border-[8px] border-amber-400 rounded-t-full border-b-0"
                style={{ clipPath: 'polygon(0 0, 40% 0, 40% 100%, 0 100%)' }} // Approx for low level
              />
              <div className="absolute -bottom-2 text-2xl font-mono font-bold text-white">{profile.hemoglobin}</div>
            </div>
            <div className="text-[10px] text-slate-500 mt-3 font-medium">Target: 8-12 g/dL</div>
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 backdrop-blur-sm flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400 mb-1 uppercase font-bold tracking-wider flex items-center gap-1.5"><Droplet className="w-3 h-3 text-teal-500" /> Total Transfusions</div>
            <div className="text-[10px] text-slate-500">142 transfusions since 2017</div>
          </div>
          <div className="text-4xl font-mono font-bold text-teal-400">
            <CountUp end={profile.transfusion_count} duration={2} />
          </div>
        </div>

        {/* Active Emergency Tracker */}
        {profile.active_request && (
          <div className="bg-slate-900/90 border-l-4 border-red-500 rounded-r-2xl border-t border-r border-b border-slate-800 p-5 relative overflow-hidden shadow-lg">
            <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/10 blur-2xl rounded-full" />
            
            <div className="flex justify-between items-center mb-5 relative z-10">
              <div className="flex items-center gap-2">
                <div className="text-sm font-bold text-white uppercase tracking-wide">Active Request</div>
                <span className="text-[10px] font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded">{profile.active_request}</span>
              </div>
              <div className="text-[9px] font-black bg-red-500/20 text-red-400 px-2 py-1 rounded-sm uppercase">Critical</div>
            </div>
            
            <div className="relative z-10 mb-4">
              {/* Chain dots visual */}
              <div className="flex items-center justify-between relative mb-2 px-1">
                <div className="absolute left-1 right-1 top-1.5 h-0.5 bg-slate-800 z-0" />
                {Array.from({ length: 8 }).map((_, i) => {
                  const d = profile.linked_donors[i];
                  const status = d?.status || 'PENDING';
                  return (
                    <div key={i} className={`relative z-10 w-3.5 h-3.5 rounded-full border-2 border-slate-900 ${
                      status === 'CONFIRMED' ? 'bg-emerald-500 shadow-[0_0_5px_rgba(16,185,129,0.5)]' : 
                      status === 'ALERTED' ? 'bg-amber-500 animate-pulse' : 
                      status === 'DECLINED' ? 'bg-red-500' : 'bg-slate-700'
                    }`} />
                  );
                })}
              </div>
              <div className="flex justify-between text-[9px] font-mono font-bold text-slate-500 uppercase px-1">
                <span className="text-emerald-400">Confirmed</span>
                <span className="text-amber-400">Alerted</span>
                <span>Pending</span>
              </div>
            </div>
            
            <p className="text-xs text-slate-300 leading-relaxed font-medium bg-slate-950/50 p-3 rounded-lg border border-slate-800 flex items-start gap-2">
              <Activity className="w-4 h-4 text-teal-400 shrink-0 mt-0.5" />
              AI agents are coordinating your donors. Estimated arrival: 45 min. Stay on this page for live updates.
            </p>
          </div>
        )}

        {/* Linked Donors Scroll */}
        <div>
          <h3 className="text-sm font-bold text-white mb-3 uppercase tracking-wider">Your Linked Donors</h3>
          <div className="flex gap-3 overflow-x-auto pb-4 -mx-4 px-4 snap-x no-scrollbar">
            {profile.linked_donors.map(donor => (
              <div key={donor.donor_id} className="w-48 min-w-[192px] bg-slate-900/60 border border-slate-800 rounded-2xl p-4 snap-start shrink-0 flex flex-col">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-full bg-slate-800 overflow-hidden border border-slate-700 shrink-0">
                    <img src={`https://api.dicebear.com/7.x/notionists/svg?seed=${donor.donor_name}`} alt="Avatar" className="w-full h-full" />
                  </div>
                  <div className="truncate">
                    <div className="font-bold text-sm text-white truncate">{donor.donor_name}</div>
                    <div className="text-[10px] text-slate-500 font-mono">{donor.donor_id}</div>
                  </div>
                </div>
                
                <div className="mb-3">
                  <div className="flex justify-between text-[10px] font-bold text-slate-400 mb-1">
                    <span>Blood Match</span>
                    <span className="text-teal-400">{Math.round(donor.antigen_score * 100)}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-teal-500" style={{ width: `${Math.round(donor.antigen_score * 100)}%` }} />
                  </div>
                </div>
                
                <div className="mt-auto pt-3 border-t border-slate-800/50 flex justify-between items-center">
                  <span className={`text-[9px] font-bold uppercase tracking-widest px-2 py-0.5 rounded ${
                    donor.status === 'CONFIRMED' ? 'bg-emerald-500/20 text-emerald-400' : 
                    donor.status === 'ALERTED' ? 'bg-amber-500/20 text-amber-400' : 
                    donor.status === 'DECLINED' ? 'bg-red-500/10 text-red-500/50 border border-red-500/20' : 
                    'bg-slate-800 text-slate-400'
                  }`}>
                    {donor.status}
                  </span>
                  <span className="text-[10px] text-slate-500 font-medium">{donor.donation_count} donations</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* History */}
        <div className="pt-2">
          <h3 className="text-sm font-bold text-white mb-3 uppercase tracking-wider">Transfusion History</h3>
          <Accordion type="single" collapsible className="w-full space-y-2">
            {profile.transfusion_history.map((tx, idx) => {
              const date = new Date(tx.date);
              const isSuccess = tx.outcome.includes('Success');
              const isMild = tx.outcome.includes('mild');
              
              return (
                <AccordionItem key={idx} value={`item-${idx}`} className="bg-slate-900/50 border border-slate-800 rounded-xl px-4">
                  <AccordionTrigger className="hover:no-underline py-4">
                    <div className="flex items-center gap-4 text-left w-full pr-2">
                      <div className="flex flex-col items-center justify-center bg-slate-950 rounded-lg p-2 min-w-[50px] border border-slate-800/50">
                        <span className="text-[10px] uppercase font-bold text-slate-500 leading-none">{date.toLocaleDateString('en-US', { month: 'short' })}</span>
                        <span className="text-lg font-mono font-bold text-white leading-none mt-1">{date.getDate()}</span>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-bold text-sm text-white">{tx.donor_name}</span>
                          <span className="px-1.5 py-0.5 bg-slate-800 text-slate-300 text-[9px] font-bold font-mono rounded">{tx.blood_type}</span>
                        </div>
                        <span className={`text-[10px] font-bold ${isMild ? 'text-amber-400' : isSuccess ? 'text-emerald-400' : 'text-red-400'}`}>
                          {tx.outcome}
                        </span>
                      </div>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="text-xs text-slate-400 pb-4 pt-1 pl-[66px]">
                    Transfusion completed at KIMS Secunderabad. No major antibodies detected post-transfusion. Donor antigen compatibility was verified via AI matching.
                  </AccordionContent>
                </AccordionItem>
              );
            })}
          </Accordion>
        </div>

      </div>
    </div>
  );
}