import { useState } from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { useEmergencySocket } from "@/hooks/useEmergencySocket";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, Activity, Users, CheckCircle, Clock, AlertTriangle, CheckCircle2, X, ArrowRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { triggerEmergency, confirmOutcome, getEmergencyTrace, type EmergencyTrace } from "@/lib/api";

const CHAIN_DOT_COLORS: Record<string, { bg: string; border: string }> = {
  CONFIRMED: { bg: "#10b981", border: "#059669" },
  COMPLETED: { bg: "#10b981", border: "#059669" },
  ALERTED:   { bg: "#f59e0b", border: "#d97706" },
  VOICE:     { bg: "#f59e0b", border: "#d97706" },
  SMS:       { bg: "#f59e0b", border: "#d97706" },
  DECLINED:  { bg: "#ef4444", border: "#dc2626" },
  PENDING:   { bg: "#cbd5e1", border: "#94a3b8" },
};

const ChainDot = ({ status, donorName, position }: { status: string, donorName: string, position: number }) => {
  const isConfirmed = status === "CONFIRMED" || status === "COMPLETED";
  const isAlerted = status === "ALERTED" || status === "VOICE" || status === "SMS";
  const colors = CHAIN_DOT_COLORS[status] ?? CHAIN_DOT_COLORS.PENDING;

  return (
    <div className="relative group flex flex-col items-center">
      <motion.div
        layout
        key={status}
        initial={{ scale: 0.6, opacity: 0 }}
        animate={{
          scale: 1,
          opacity: 1,
          backgroundColor: colors.bg,
          borderColor: colors.border,
          boxShadow: isConfirmed ? "0 0 8px rgba(16,185,129,0.4)" : "0 0 0px transparent",
        }}
        transition={{ type: "spring", stiffness: 400, damping: 22 }}
        className={`w-4 h-4 rounded-full border-2 ${isAlerted ? "animate-pulse" : ""}`}
      />
      <span className="text-[10px] font-mono mt-1 text-muted-foreground">{position}</span>
      <div className="absolute bottom-full mb-2 bg-slate-800 text-white text-[10px] px-2 py-1 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-10 font-sans shadow-lg">
        <span className="font-bold">{donorName}</span> • {status}
      </div>
    </div>
  );
};

export default function Emergency() {
  const { emergencies, chainBreak } = useEmergencySocket();
  const [isCreating, setIsCreating] = useState(false);
  const [open, setOpen] = useState(false);
  const [resolving, setResolving] = useState<string | null>(null);
  const [traceDrawer, setTraceDrawer] = useState<{ open: boolean; trace: EmergencyTrace | null; loading: boolean }>({ open: false, trace: null, loading: false });

  const openTrace = async (requestId: string) => {
    setTraceDrawer({ open: true, trace: null, loading: true });
    try {
      const trace = await getEmergencyTrace(requestId);
      setTraceDrawer({ open: true, trace, loading: false });
    } catch {
      toast.error("Failed to load trace");
      setTraceDrawer({ open: false, trace: null, loading: false });
    }
  };

  const handleCreate = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsCreating(true);
    try {
      const formData = new FormData(e.currentTarget);
      await triggerEmergency({
        patient_id: formData.get("patient_id") as string,
        blood_type: formData.get("blood_type") as string,
        city: formData.get("city") as string,
        ward: formData.get("ward") as string,
        hospital: "KIMS Secunderabad"
      });
      toast.success("Emergency request created. AI Agents dispatched.");
      setOpen(false);
    } catch (err) {
      toast.error("Failed to create emergency");
    } finally {
      setIsCreating(false);
    }
  };

  const handleResolve = async (requestId: string) => {
    setResolving(requestId);
    try {
      await confirmOutcome(requestId);
      toast.success(`Emergency ${requestId} marked as resolved.`);
    } catch {
      toast.error("Failed to mark as resolved — check server logs.");
    } finally {
      setResolving(null);
    }
  };

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight">Emergency Operations Center</h1>
            <div className="flex items-center gap-1.5 bg-red-100 dark:bg-red-950/40 text-red-600 dark:text-red-400 px-2.5 py-0.5 rounded-full border border-red-200 dark:border-red-900/50">
              <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
              <span className="text-[10px] font-mono tracking-wider font-bold">LIVE</span>
            </div>
          </div>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button className="bg-teal-600 hover:bg-teal-700 text-white gap-2 shadow-sm">
                <Plus className="w-4 h-4" /> New Emergency
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>Declare New Emergency</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleCreate} className="space-y-4 pt-4">
                <div className="space-y-2">
                  <Label>Patient ID</Label>
                  <Input name="patient_id" required placeholder="e.g., P-10234" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Blood Type</Label>
                    <Select name="blood_type" required defaultValue="B+">
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {["A+","A-","B+","B-","AB+","AB-","O+","O-"].map(bt => (
                          <SelectItem key={bt} value={bt}>{bt}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>City</Label>
                    <Select name="city" required defaultValue="Hyderabad">
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Hyderabad">Hyderabad</SelectItem>
                        <SelectItem value="Mumbai">Mumbai</SelectItem>
                        <SelectItem value="Bangalore">Bangalore</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Ward / Department</Label>
                  <Input name="ward" required placeholder="Thalassemia Day Care" />
                </div>
                <Button type="submit" disabled={isCreating} className="w-full bg-red-600 hover:bg-red-700 text-white mt-4">
                  {isCreating ? "Dispatching AI Agents..." : "Trigger Emergency Protocol"}
                </Button>
              </form>
            </DialogContent>
          </Dialog>

          {/* Demo Trigger Button — only visible when staff token is set */}
          {import.meta.env.VITE_STAFF_TOKEN && (
            <Button
              size="sm"
              variant="outline"
              className="border-dashed border-amber-500/50 text-amber-600 dark:text-amber-400 hover:bg-amber-500/10"
              onClick={async () => {
                try {
                  await triggerEmergency({
                    patient_id: "P-10026",
                    blood_type: "B+",
                    city: "Hyderabad",
                    ward: "Thalassemia Day Care",
                    hospital: "KIMS Secunderabad"
                  });
                  toast.success("Demo emergency triggered! Watch the chain build in real-time.");
                } catch (err: any) {
                  toast.error("Demo trigger failed: " + (err?.message || "Unknown error"));
                }
              }}
            >
              ⚡ Demo Emergency
            </Button>
          )}
        </div>
        <AnimatePresence>
          {chainBreak && (
            <motion.div 
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-red-50 dark:bg-red-950/40 border-l-4 border-l-red-600 border-t border-r border-b border-red-200 dark:border-red-900/50 p-4 rounded-xl flex items-center gap-4 shadow-md overflow-hidden relative"
            >
              <div className="absolute top-0 right-0 w-32 h-full bg-gradient-to-l from-red-500/10 to-transparent" />
              <div className="bg-red-100 dark:bg-red-900/50 p-2 rounded-full">
                <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400 animate-pulse" />
              </div>
              <div>
                <p className="font-bold text-red-900 dark:text-red-300">Chain break detected at position {chainBreak.position} — Auto-repair agent engaged</p>
                <p className="text-sm text-red-700 dark:text-red-400 mt-0.5">Patient {chainBreak.patient_id} • AI is contacting backup donors immediately.</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="h-28 flex flex-col justify-between overflow-hidden relative group border-slate-200 dark:border-slate-800">
            <CardContent className="p-4 flex items-center justify-between z-10">
              <div>
                <p className="text-sm text-muted-foreground font-medium mb-1">Active Emergencies</p>
                <p className="text-3xl font-bold">{emergencies.length}</p>
              </div>
              <div className="p-3 bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400 rounded-xl group-hover:scale-110 transition-transform">
                <Activity className="w-5 h-5" />
              </div>
            </CardContent>
            <div className="absolute bottom-0 left-0 w-full h-8 flex items-end gap-1 px-4 opacity-20">
              {[2,3,4,3,5,6].map((h, i) => <div key={i} className="flex-1 bg-red-500 rounded-t-sm" style={{height: `${h*4}px`}} />)}
            </div>
          </Card>
          <Card className="h-28 flex flex-col justify-between overflow-hidden relative group border-slate-200 dark:border-slate-800">
            <CardContent className="p-4 flex items-center justify-between z-10">
              <div>
                <p className="text-sm text-muted-foreground font-medium mb-1">Donors Alerted</p>
                <p className="text-3xl font-bold">{emergencies.reduce((sum, em) => sum + em.chain.filter(c => ['ALERTED','SMS','VOICE','CONFIRMED','COMPLETED'].includes(c.status)).length, 0)}</p>
              </div>
              <div className="p-3 bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400 rounded-xl group-hover:scale-110 transition-transform">
                <Users className="w-5 h-5" />
              </div>
            </CardContent>
            <div className="absolute bottom-0 left-0 w-full h-8 flex items-end gap-1 px-4 opacity-20">
              {[5,7,12,18,20,24].map((h, i) => <div key={i} className="flex-1 bg-amber-500 rounded-t-sm" style={{height: `${(h/24)*24}px`}} />)}
            </div>
          </Card>
          <Card className="h-28 flex flex-col justify-between overflow-hidden relative group border-slate-200 dark:border-slate-800">
            <CardContent className="p-4 flex items-center justify-between z-10">
              <div>
                <p className="text-sm text-muted-foreground font-medium mb-1">Confirmed Today</p>
                <p className="text-3xl font-bold">{emergencies.reduce((sum, em) => sum + em.chain.filter(c => c.status === 'CONFIRMED' || c.status === 'COMPLETED').length, 0)}</p>
              </div>
              <div className="p-3 bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400 rounded-xl group-hover:scale-110 transition-transform">
                <CheckCircle className="w-5 h-5" />
              </div>
            </CardContent>
            <div className="absolute bottom-0 left-0 w-full h-8 flex items-end gap-1 px-4 opacity-20">
              {[1,2,5,7,8,11].map((h, i) => <div key={i} className="flex-1 bg-emerald-500 rounded-t-sm" style={{height: `${(h/11)*24}px`}} />)}
            </div>
          </Card>
          <Card className="h-28 flex flex-col justify-between overflow-hidden relative group border-slate-200 dark:border-slate-800">
            <CardContent className="p-4 flex items-center justify-between z-10">
              <div>
                <p className="text-sm text-muted-foreground font-medium mb-1">Chain Size</p>
                <p className="text-3xl font-bold font-mono text-teal-600 dark:text-teal-400">{emergencies.length > 0 ? Math.round(emergencies.reduce((sum, em) => sum + em.chain.length, 0) / emergencies.length) : 0}</p>
              </div>
              <div className="p-3 bg-teal-100 text-teal-600 dark:bg-teal-900/30 dark:text-teal-400 rounded-xl group-hover:scale-110 transition-transform">
                <Clock className="w-5 h-5" />
              </div>
            </CardContent>
            <div className="absolute bottom-0 left-0 w-full h-8 flex items-end gap-1 px-4 opacity-20">
              {[35,30,26,22,19,18].map((h, i) => <div key={i} className="flex-1 bg-teal-500 rounded-t-sm" style={{height: `${(h/35)*24}px`}} />)}
            </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {emergencies.map(em => (
            <Card key={em.request_id} className={`overflow-hidden border-0 shadow-sm relative`}>
              <div className={`absolute top-0 left-0 w-1.5 h-full ${em.priority === 'CRITICAL' ? 'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]' : em.priority === 'HIGH' ? 'bg-amber-500' : 'bg-emerald-500'}`} />
              
              <CardHeader className="pb-4 border-b bg-slate-50/50 dark:bg-slate-900/20 pl-6">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs font-mono text-slate-500 bg-slate-200/50 dark:bg-slate-800 px-2 py-0.5 rounded">{em.request_id}</span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase flex items-center gap-1.5 ${
                        em.priority === 'CRITICAL' ? 'bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 shadow-[0_0_8px_rgba(239,68,68,0.2)]' : 
                        em.priority === 'HIGH' ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20' : 
                        'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20'
                      }`}>
                        {em.priority === 'CRITICAL' && <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />}
                        {em.priority}
                      </span>
                    </div>
                    <CardTitle className="text-xl font-mono tracking-tight mb-1">Patient {em.patient_id}</CardTitle>
                    <p className="text-sm font-medium text-muted-foreground">{em.hospital_name}</p>
                    <p className="text-xs text-muted-foreground opacity-80">{em.ward}</p>
                  </div>
                  
                  {/* Hexagon Blood Type Badge */}
                  <div className="relative w-16 h-16 flex items-center justify-center -mt-1 mr-2">
                    <div className="absolute inset-0 bg-gradient-to-br from-slate-100 to-slate-200 dark:from-slate-800 dark:to-slate-900 rotate-45 rounded-xl border border-slate-300 dark:border-slate-700 shadow-sm" />
                    <div className="absolute inset-1 bg-white dark:bg-slate-950 rotate-45 rounded-lg border border-slate-100 dark:border-slate-800" />
                    <span className="relative z-10 text-2xl font-mono font-black text-slate-800 dark:text-slate-200">{em.blood_type}</span>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent className="pt-5 pl-6 pb-6">
                <div className="space-y-6">
                  {/* Mini Timeline */}
                  <div className="flex items-center gap-4 text-[10px] text-muted-foreground font-mono">
                    <div className="flex items-center gap-1.5"><div className="w-1.5 h-1.5 rounded-full bg-slate-400" /> Created</div>
                    <div className="w-4 border-t border-dashed border-slate-300 dark:border-slate-700" />
                    <div className="flex items-center gap-1.5"><div className="w-1.5 h-1.5 rounded-full bg-amber-400" /> AI Alerted</div>
                    <div className="w-4 border-t border-dashed border-slate-300 dark:border-slate-700" />
                    <div className="flex items-center gap-1.5"><div className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Confirmed</div>
                  </div>

                  {/* Chain Visualization */}
                  <div>
                    <div className="flex justify-between items-end mb-3">
                      <div className="text-xs font-bold uppercase tracking-wider text-slate-500">AI Outreach Chain</div>
                      <div className="text-[10px] font-mono text-muted-foreground bg-secondary px-2 py-0.5 rounded">
                        {em.chain.filter(c=>c.status==='CONFIRMED').length} confirmed / {em.chain.filter(c=>c.status==='ALERTED').length} alerted / {em.chain.filter(c=>c.status==='PENDING').length} pending
                      </div>
                    </div>
                    
                    <div className="relative flex items-center justify-between w-full px-2 py-4 bg-slate-50/50 dark:bg-slate-900/30 rounded-lg border border-slate-100 dark:border-slate-800">
                      {/* Connecting lines drawn behind dots */}
                      <div className="absolute top-6 left-6 right-6 h-0.5 flex">
                        {em.chain.slice(0,-1).map((node, i) => {
                          const isConfirmed = node.status === 'CONFIRMED' || em.chain[i+1].status === 'CONFIRMED';
                          const isAlerted = node.status === 'ALERTED' || em.chain[i+1].status === 'ALERTED';
                          return (
                            <div key={i} className={`flex-1 h-full ${
                              isConfirmed ? 'bg-emerald-500' : 
                              isAlerted ? 'border-t-[2px] border-dashed border-amber-500/50' : 
                              'border-t-[2px] border-dotted border-slate-300 dark:border-slate-700'
                            }`} />
                          );
                        })}
                      </div>
                      
                      {em.chain.map(node => (
                        <ChainDot key={node.donor_id} status={node.status} donorName={node.donor_name} position={node.chain_position} />
                      ))}
                    </div>
                  </div>

                  {/* Mark Resolved button — only for chains with at least one confirmed donor */}
                  {em.chain.some(c => c.status === 'CONFIRMED' || c.status === 'COMPLETED') && (
                    <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
                      <Button
                        size="sm"
                        variant="outline"
                        className="w-full gap-2 border-emerald-200 dark:border-emerald-900/50 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-950/30"
                        disabled={resolving === em.request_id}
                        onClick={() => handleResolve(em.request_id)}
                      >
                        {resolving === em.request_id ? (
                          <span className="flex items-center gap-2"><div className="w-3 h-3 border-2 border-current/30 border-t-current rounded-full animate-spin" /> Marking...</span>
                        ) : (
                          <><CheckCircle2 className="w-3.5 h-3.5" /> Mark Resolved</>
                        )}
                      </Button>
                    </div>
                  )}

                  {/* View AI Trace button */}
                  <div className="pt-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      className="w-full gap-2 text-xs text-slate-500 hover:text-indigo-500"
                      onClick={() => openTrace(em.request_id)}
                    >
                      <Activity className="w-3.5 h-3.5" /> View AI Agent Trace
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Trace Drawer */}
        <AnimatePresence>
          {traceDrawer.open && (
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="fixed top-0 right-0 h-full w-[450px] bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 z-50 shadow-2xl overflow-y-auto"
            >
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-lg font-bold flex items-center gap-2">
                    <Activity className="w-5 h-5 text-indigo-500" /> Agent Execution Trace
                  </h2>
                  <Button size="icon" variant="ghost" onClick={() => setTraceDrawer({ open: false, trace: null, loading: false })}>
                    <X className="w-4 h-4" />
                  </Button>
                </div>

                {traceDrawer.loading && (
                  <div className="flex items-center justify-center py-12">
                    <div className="w-6 h-6 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
                  </div>
                )}

                {traceDrawer.trace && (
                  <div className="space-y-4">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-500 font-mono">{traceDrawer.trace.request_id}</span>
                      <span className={`text-xs font-bold px-2 py-0.5 rounded ${traceDrawer.trace.outcome === 'SUCCESS' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'}`}>
                        {traceDrawer.trace.outcome}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500">Total: {traceDrawer.trace.total_ms}ms</div>

                    <div className="space-y-3 pt-4">
                      {traceDrawer.trace.nodes.map((node, i) => (
                        <div key={i} className="flex items-center gap-3">
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${node.status === 'success' ? 'bg-emerald-100 dark:bg-emerald-900/30' : node.status === 'fallback' ? 'bg-amber-100 dark:bg-amber-900/30' : 'bg-red-100 dark:bg-red-900/30'}`}>
                            {node.status === 'success' ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : node.status === 'fallback' ? <AlertTriangle className="w-4 h-4 text-amber-600" /> : <X className="w-4 h-4 text-red-600" />}
                          </div>
                          <div className="flex-1">
                            <div className="text-sm font-medium">{node.name}</div>
                            <div className="text-[10px] text-slate-500 font-mono">{node.duration_ms}ms</div>
                          </div>
                          {i < traceDrawer.trace!.nodes.length - 1 && <ArrowRight className="w-3 h-3 text-slate-300" />}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </DashboardLayout>
  );
}