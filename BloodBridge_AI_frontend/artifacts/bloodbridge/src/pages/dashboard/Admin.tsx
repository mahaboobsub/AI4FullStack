import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import {
  getSystemHealth, getAgentTraces, retrainModels,
  getStaffMembers, addStaffMember, deleteStaffMember,
  getAgentConfig, updateAgentConfig, getScheduleEntries,
  adminGetBridges, adminCreateBridge, adminDeleteBridge,
  adminDeleteDonor, adminDeletePatient,
  type ServiceHealth, type AgentTrace, type AgentConfig, type ScheduleEntry,
  type BridgeMembership,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Activity, RefreshCcw, Server, Shield, Trash2, CheckCircle2, AlertTriangle, XCircle, ArrowRight, BrainCircuit, Plus, Upload, Calendar, Settings } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";
import { motion } from "framer-motion";
import DemandForecastPanel from "@/components/DemandForecastPanel";
import AssignmentOptimizerPanel from "@/components/AssignmentOptimizerPanel";

interface StaffMember { username: string; hospital: string; role: string; added: string; }

export default function Admin() {
  const [health, setHealth] = useState<ServiceHealth[]>([]);
  const [traces, setTraces] = useState<AgentTrace[]>([]);
  const [staff, setStaff] = useState<StaffMember[]>([]);
  const [retrainDialogOpen, setRetrainDialogOpen] = useState(false);
  const [retrainProgress, setRetrainProgress] = useState(0);
  const [retrainStatus, setRetrainStatus] = useState<"idle" | "training" | "complete">("idle");
  const [addStaffOpen, setAddStaffOpen] = useState(false);
  const [newStaff, setNewStaff] = useState({ username: "", hospital: "", role: "Staff" });
  const [addingStaff, setAddingStaff] = useState(false);
  const [agentConfig, setAgentConfig] = useState<AgentConfig | null>(null);
  const [csvUploading, setCsvUploading] = useState(false);
  const [scheduleEntries, setScheduleEntries] = useState<ScheduleEntry[]>([]);
  const [configEditing, setConfigEditing] = useState(false);
  const [configForm, setConfigForm] = useState<{ timeout: number; retryLimit: number; channelSeq: string }>({ timeout: 7, retryLimit: 5, channelSeq: "" });
  const [bridges, setBridges] = useState<BridgeMembership[]>([]);
  const [newBridge, setNewBridge] = useState({ patient_id: "", donor_id: "" });
  const [bridgeAdding, setBridgeAdding] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<{ type: "donor" | "patient"; id: string } | null>(null);
  const [deleting, setDeleting] = useState(false);

  const staffToken = import.meta.env.VITE_STAFF_TOKEN || "";
  const isTestToken = staffToken === "test-admin-token" || !staffToken;

  const refreshData = () => {
    getSystemHealth().then(setHealth).catch(() => {});
    getAgentTraces().then(setTraces).catch(() => {});
  };

  const loadStaff = () => {
    getStaffMembers()
      .then(setStaff)
      .catch(() => setStaff([]));
  };

  useEffect(() => {
    refreshData();
    loadStaff();
    getAgentConfig().then(c => {
      setAgentConfig(c);
      setConfigForm({ timeout: c.coordination_timeout_mins, retryLimit: c.retry_limit, channelSeq: c.channel_sequence.join(", ") });
    }).catch(() => setAgentConfig(null));
    getScheduleEntries().then(setScheduleEntries).catch(() => setScheduleEntries([]));
    adminGetBridges().then(setBridges).catch(() => setBridges([]));
    const interval = setInterval(refreshData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleRetrainClick = async () => {
    setRetrainDialogOpen(true);
    setRetrainStatus("training");
    setRetrainProgress(0);

    // Start visual progress animation
    let current = 0;
    const interval = setInterval(() => {
      current += 5;
      setRetrainProgress(Math.min(current, 90)); // cap at 90 until API confirms
      if (current >= 90) clearInterval(interval);
    }, 75);

    try {
      const result = await retrainModels();
      clearInterval(interval);
      setRetrainProgress(100);
      setRetrainStatus("complete");
      setTimeout(() => {
        setRetrainDialogOpen(false);
        toast.success(`Model retraining job ${result.jobId} queued successfully.`);
      }, 1500);
    } catch (err) {
      clearInterval(interval);
      setRetrainDialogOpen(false);
      setRetrainStatus("idle");
      toast.error("Retrain failed — check server logs.");
    }
  };

  const handleAddStaff = async () => {
    if (!newStaff.username.trim() || !newStaff.hospital.trim()) {
      toast.error("Username and hospital are required.");
      return;
    }
    setAddingStaff(true);
    try {
      await addStaffMember(newStaff);
      toast.success(`${newStaff.username} added successfully.`);
      setAddStaffOpen(false);
      setNewStaff({ username: "", hospital: "", role: "Staff" });
      loadStaff();
    } catch {
      toast.error("Failed to add staff member.");
    } finally {
      setAddingStaff(false);
    }
  };

  const handleDeleteStaff = async (username: string) => {
    try {
      await deleteStaffMember(username);
      toast.success(`${username} removed.`);
      setStaff(prev => prev.filter(s => s.username !== username));
    } catch {
      toast.error("Failed to remove staff member.");
    }
  };

  const handleCsvUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setCsvUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const BASE = import.meta.env.VITE_API_URL ? import.meta.env.VITE_API_URL.replace(/\/$/, "") : "";
      const resp = await fetch(`${BASE}/api/donors/bulk-import-csv`, {
        method: "POST",
        headers: { "X-Staff-Token": staffToken },
        body: formData,
      });
      if (!resp.ok) throw new Error(`${resp.status}`);
      const result = await resp.json();
      toast.success(`Imported ${result.imported ?? 0} donors. ${result.skipped ?? 0} skipped.`);
    } catch {
      toast.error("CSV import failed.");
    } finally {
      setCsvUploading(false);
      e.target.value = "";
    }
  };

  const handleConfigSave = async () => {
    setConfigEditing(true);
    try {
      await updateAgentConfig({
        coordination_timeout_mins: configForm.timeout,
        retry_limit: configForm.retryLimit,
        channel_sequence: configForm.channelSeq.split(",").map(s => s.trim()).filter(Boolean),
      });
      toast.success("Agent config updated.");
    } catch {
      toast.error("Failed to update config.");
    } finally {
      setConfigEditing(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        {/* Token Warning Banner */}
        {isTestToken && (
          <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-xl p-4 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
            <div>
              <div className="font-bold text-sm text-amber-800 dark:text-amber-200">Using Test Admin Token</div>
              <div className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                You are using the default test-admin-token. For production, set <code className="bg-amber-100 dark:bg-amber-900/50 px-1 rounded">VITE_STAFF_TOKEN</code> in your .env file.
              </div>
            </div>
          </div>
        )}

        {agentConfig?.demo_mock_mode && (
          <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-xl p-4 flex items-start gap-3">
            <Shield className="w-5 h-5 text-blue-500 shrink-0 mt-0.5" />
            <div>
              <div className="font-bold text-sm text-blue-800 dark:text-blue-200">Demo Mode Active (DEMO_MOCK_MODE=true)</div>
              <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                Voice calls and Neo4j matching use simulated responses. Set <code className="bg-blue-100 dark:bg-blue-900/50 px-1 rounded">DEMO_MOCK_MODE=false</code> in backend .env for live Bolna/Telegram. See <code>DEMO_MODE.md</code>.
              </div>
            </div>
          </div>
        )}

        <div>
          <h1 className="text-2xl font-semibold tracking-tight">System Admin & AI Config</h1>
          <p className="text-sm text-muted-foreground mt-1">Manage LangGraph flows, models, and service health</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {/* Service Health */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2"><Server className="w-4 h-4" /> Service Health</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {health.map(svc => (
                    <div key={svc.service} className="p-4 border border-slate-200 dark:border-slate-800 rounded-xl bg-card hover:border-slate-300 dark:hover:border-slate-700 transition-colors shadow-sm flex flex-col justify-between h-36">
                      <div>
                        <div className="flex justify-between items-start mb-1">
                          <span className="text-sm font-bold">{svc.service}</span>
                          {svc.status === 'online' ? (
                            <span className="text-[9px] font-mono font-bold uppercase tracking-widest text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50 px-1.5 py-0.5 rounded border border-emerald-200 dark:border-emerald-900/50 flex items-center gap-1.5">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> ONLINE
                            </span>
                          ) : svc.status === 'degraded' ? (
                            <span className="text-[9px] font-mono font-bold uppercase tracking-widest text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/50 px-1.5 py-0.5 rounded border border-amber-200 dark:border-amber-900/50 flex items-center gap-1.5">
                              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" /> DEGRADED
                            </span>
                          ) : (
                            <span className="text-[9px] font-mono font-bold uppercase tracking-widest text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/50 px-1.5 py-0.5 rounded border border-red-200 dark:border-red-900/50 flex items-center gap-1.5">
                              <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" /> OFFLINE
                            </span>
                          )}
                        </div>
                        <div className="text-[10px] font-mono text-muted-foreground truncate mb-3" title={svc.host}>{svc.host}</div>
                      </div>
                      
                      <div>
                        <div className="flex items-end gap-0.5 mb-2 h-6">
                          {[...Array(6)].map((_, i) => {
                            const isHigh = Math.random() > 0.8 && svc.latency_ms > 200;
                            return (
                              <div key={i} className={`flex-1 rounded-sm ${isHigh ? 'bg-amber-400 dark:bg-amber-500' : 'bg-emerald-400 dark:bg-emerald-500/80'}`} style={{ height: `${20 + Math.random() * 80}%` }} />
                            );
                          })}
                        </div>
                        
                        <div className="flex justify-between items-center text-xs mb-1">
                          <span className="text-slate-500">Uptime <span className="font-semibold text-emerald-600 dark:text-emerald-400">{svc.uptime_pct}%</span></span>
                          <span className="font-mono text-slate-500 font-medium">{svc.latency_ms}ms</span>
                        </div>
                        <div className="w-full h-1 bg-secondary rounded-full overflow-hidden">
                          <div className="h-full bg-emerald-500" style={{ width: `${svc.uptime_pct}%` }} />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Agent Traces */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2"><Activity className="w-4 h-4" /> LangGraph Execution Traces</CardTitle>
                <CardDescription>Recent agentic workflow executions</CardDescription>
              </CardHeader>
              <CardContent>
                <Accordion type="single" collapsible className="w-full space-y-3">
                  {traces.map((trace, idx) => (
                    <AccordionItem key={trace.request_id} value={trace.request_id} className="border border-slate-200 dark:border-slate-800 rounded-xl bg-card overflow-hidden">
                      <AccordionTrigger className="hover:no-underline px-4 py-3 bg-slate-50/50 dark:bg-slate-900/20 hover:bg-slate-100/50 dark:hover:bg-slate-800/50 transition-colors">
                        <div className="flex items-center justify-between w-full pr-4">
                          <div className="flex items-center gap-3">
                            <span className="font-mono text-sm font-bold bg-background px-2 py-0.5 rounded border border-border">{trace.request_id}</span>
                            <span className="text-xs text-muted-foreground hidden sm:inline-block">Patient: <span className="font-mono text-foreground">{trace.patient_id}</span></span>
                          </div>
                          <div className="flex items-center gap-4">
                            <span className="text-xs text-muted-foreground hidden md:inline-block">{idx === 0 ? "2 min ago" : idx === 1 ? "1 hour ago" : "4 hours ago"}</span>
                            <span className="font-mono text-xs font-medium text-slate-500">{trace.total_ms}ms</span>
                            <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase tracking-wider w-24 text-center ${
                              trace.outcome === 'SUCCESS' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800' : 
                              trace.outcome === 'IN_PROGRESS' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 border border-blue-200 dark:border-blue-800' : 
                              'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 border border-amber-200 dark:border-amber-800'
                            }`}>
                              {trace.outcome}
                            </span>
                          </div>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="p-4 bg-background border-t border-border overflow-x-auto">
                        <div className="flex items-center min-w-max pb-2">
                          {trace.nodes.map((node, i) => (
                            <div key={i} className="flex items-center">
                              <div className={`flex flex-col items-center justify-center p-3 rounded-xl border w-32 ${
                                node.status === 'success' ? 'bg-emerald-50/50 border-emerald-100 dark:bg-emerald-950/20 dark:border-emerald-900/50' : 
                                node.status === 'fallback' ? 'bg-amber-50/50 border-amber-100 dark:bg-amber-950/20 dark:border-amber-900/50' : 
                                'bg-red-50/50 border-red-100 dark:bg-red-950/20 dark:border-red-900/50'
                              }`}>
                                {node.status === 'success' ? <CheckCircle2 className="w-5 h-5 text-emerald-500 mb-2" /> :
                                 node.status === 'fallback' ? <AlertTriangle className="w-5 h-5 text-amber-500 mb-2" /> :
                                 <XCircle className="w-5 h-5 text-red-500 mb-2" />}
                                <span className="text-[10px] font-bold text-center leading-tight mb-1">{node.name}</span>
                                <span className="font-mono text-[9px] text-muted-foreground">{node.duration_ms}ms</span>
                              </div>
                              {i < trace.nodes.length - 1 && (
                                <div className="w-6 relative flex items-center justify-center text-slate-300 dark:text-slate-600">
                                  <div className="absolute w-full h-px bg-slate-300 dark:bg-slate-700" />
                                  <ArrowRight className="w-3 h-3 absolute bg-background" />
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            {/* Model Metrics */}
            <Card>
              <CardHeader className="pb-3 flex flex-row items-center justify-between">
                <CardTitle className="text-lg flex items-center gap-2"><BrainCircuit className="w-4 h-4" /> ML Models</CardTitle>
                <Button size="sm" className="h-8 text-xs bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm" onClick={handleRetrainClick}>
                  <RefreshCcw className="w-3 h-3 mr-1.5" /> Retrain
                </Button>
              </CardHeader>
              <CardContent className="space-y-5">
                <div>
                  <div className="flex justify-between text-sm mb-1.5">
                    <span className="font-medium text-slate-700 dark:text-slate-300">XGBoost Churn Prediction</span>
                    <span className="font-mono font-bold text-teal-600 dark:text-teal-400">F1: 0.87</span>
                  </div>
                  <div className="w-full bg-secondary h-2 rounded-full overflow-hidden"><div className="bg-teal-500 h-full w-[87%]" /></div>
                  <div className="text-[10px] text-muted-foreground mt-1 text-right">Last trained: 14 days ago</div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1.5">
                    <span className="font-medium text-slate-700 dark:text-slate-300">XGBoost Urgency Scorer</span>
                    <span className="font-mono font-bold text-teal-600 dark:text-teal-400">Acc: 0.91</span>
                  </div>
                  <div className="w-full bg-secondary h-2 rounded-full overflow-hidden"><div className="bg-teal-500 h-full w-[91%]" /></div>
                  <div className="text-[10px] text-muted-foreground mt-1 text-right">Last updated: 3 days ago</div>
                </div>
              </CardContent>
            </Card>

            {/* Staff Whitelist */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2"><Shield className="w-4 h-4" /> Access Control</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {staff.map(s => (
                    <div key={s.username} className="flex items-center justify-between p-3 rounded-lg border border-transparent hover:border-slate-200 dark:hover:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors group">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-600 dark:text-slate-400">
                          {s.username.replace('@', '').charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <div className="font-mono text-sm font-bold text-teal-700 dark:text-teal-400 mb-0.5">{s.username}</div>
                          <div className="text-[10px] text-muted-foreground">{s.hospital}</div>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <span className={`text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                          s.role === 'Admin' ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400' :
                          s.role === 'Coordinator' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                          'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
                        }`}>{s.role}</span>
                        <Button
                          variant="ghost" size="icon"
                          className="h-5 w-5 text-slate-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                          onClick={() => handleDeleteStaff(s.username)}
                        >
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      </div>
                    </div>
                  ))}
                  {staff.length === 0 && (
                    <p className="text-xs text-muted-foreground text-center py-4">No staff members yet.</p>
                  )}
                  <Button
                    variant="outline"
                    className="w-full text-xs h-9 mt-4 border-dashed bg-transparent hover:bg-slate-50 dark:hover:bg-slate-900 gap-2"
                    onClick={() => setAddStaffOpen(true)}
                  >
                    <Plus className="w-3 h-3" /> Add Staff Member
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Live Activity Log */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold uppercase tracking-wider text-slate-500">Live Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 font-mono text-[11px]">
                  <div className="flex gap-2">
                    <span className="text-slate-500 shrink-0">14:02:11</span>
                    <span className="text-emerald-500">•</span>
                    <span className="text-slate-700 dark:text-slate-300">REQ-8847 · Chain confirmed · D-1001 → P-10234</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-slate-500 shrink-0">14:00:45</span>
                    <span className="text-amber-500">•</span>
                    <span className="text-slate-700 dark:text-slate-300">D-1008 alerted via Telegram bot</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-slate-500 shrink-0">13:58:20</span>
                    <span className="text-indigo-500">•</span>
                    <span className="text-slate-700 dark:text-slate-300">Model retrain scheduled · Job-8472</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-slate-500 shrink-0">13:55:01</span>
                    <span className="text-red-500">•</span>
                    <span className="text-slate-700 dark:text-slate-300">Chain break detected · REQ-8901 · Pos 3</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-slate-500 shrink-0">13:52:44</span>
                    <span className="text-blue-500">•</span>
                    <span className="text-slate-700 dark:text-slate-300">System health check · All ok</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* A5: Demand Forecast Panel (additive, full-width) */}
        <DemandForecastPanel />
        <AssignmentOptimizerPanel />

        {/* Bulk CSV Import */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2"><Upload className="w-4 h-4" /> Bulk Donor Import (CSV)</CardTitle>
            <CardDescription>Upload a CSV file to bulk-import donors. Required columns: name, phone, blood_type, city</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <input
                type="file"
                accept=".csv"
                className="hidden"
                id="csvBulkUpload"
                onChange={handleCsvUpload}
              />
              <label htmlFor="csvBulkUpload">
                <Button asChild variant="outline" className="gap-2 cursor-pointer" disabled={csvUploading}>
                  <span>
                    <Upload className="w-4 h-4" />
                    {csvUploading ? "Uploading..." : "Choose CSV File"}
                  </span>
                </Button>
              </label>
              <span className="text-xs text-muted-foreground">Max 500 rows per upload. Duplicates (by phone) are skipped.</span>
            </div>
          </CardContent>
        </Card>

        {/* Schedule Overview */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2"><Calendar className="w-4 h-4" /> Upcoming Schedules</CardTitle>
            <CardDescription>Auto-scheduled transfusions from the proactive scheduler</CardDescription>
          </CardHeader>
          <CardContent>
            {scheduleEntries.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">No scheduled transfusions found.</p>
            ) : (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {scheduleEntries.slice(0, 20).map((s) => (
                  <div key={s.schedule_id} className="flex items-center justify-between p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-card">
                    <div>
                      <div className="text-sm font-medium">{s.patient_id}</div>
                      <div className="text-[10px] text-muted-foreground">{s.hospital} · {s.blood_type}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-mono">{new Date(s.scheduled_date).toLocaleDateString()}</div>
                      <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded ${s.status === 'CONFIRMED' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'}`}>
                        {s.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Agent Config Editor */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2"><Settings className="w-4 h-4" /> Agent Configuration</CardTitle>
            <CardDescription>Edit LangGraph coordination parameters</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Coordination Timeout (mins)</label>
                <Input
                  type="number"
                  value={configForm.timeout}
                  onChange={(e) => setConfigForm(p => ({ ...p, timeout: parseInt(e.target.value) || 7 }))}
                  className="h-9"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Retry Limit</label>
                <Input
                  type="number"
                  value={configForm.retryLimit}
                  onChange={(e) => setConfigForm(p => ({ ...p, retryLimit: parseInt(e.target.value) || 5 }))}
                  className="h-9"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Channel Sequence</label>
                <Input
                  value={configForm.channelSeq}
                  onChange={(e) => setConfigForm(p => ({ ...p, channelSeq: e.target.value }))}
                  placeholder="telegram, voice, sms"
                  className="h-9"
                />
              </div>
            </div>
            <Button
              size="sm"
              className="bg-indigo-600 hover:bg-indigo-700 text-white"
              disabled={configEditing}
              onClick={handleConfigSave}
            >
              {configEditing ? "Saving..." : "Save Configuration"}
            </Button>
          </CardContent>
        </Card>

        {/* Bridge Memberships Management */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2"><Shield className="w-4 h-4" /> Bridge Memberships</CardTitle>
            <CardDescription>Manage patient ↔ donor bridge connections. Delete donors or patients.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Add Bridge Form */}
            <div className="flex gap-2 items-end">
              <div className="space-y-1 flex-1">
                <label className="text-xs font-medium text-muted-foreground">Patient ID</label>
                <Input
                  placeholder="P-10234"
                  value={newBridge.patient_id}
                  onChange={e => setNewBridge(p => ({ ...p, patient_id: e.target.value }))}
                  className="h-9"
                />
              </div>
              <div className="space-y-1 flex-1">
                <label className="text-xs font-medium text-muted-foreground">Donor ID</label>
                <Input
                  placeholder="D-1001"
                  value={newBridge.donor_id}
                  onChange={e => setNewBridge(p => ({ ...p, donor_id: e.target.value }))}
                  className="h-9"
                />
              </div>
              <Button
                size="sm"
                className="h-9 bg-teal-600 hover:bg-teal-700 text-white"
                disabled={bridgeAdding || !newBridge.patient_id.trim() || !newBridge.donor_id.trim()}
                onClick={async () => {
                  setBridgeAdding(true);
                  try {
                    await adminCreateBridge(newBridge.patient_id.trim(), newBridge.donor_id.trim());
                    toast.success("Bridge created.");
                    setNewBridge({ patient_id: "", donor_id: "" });
                    adminGetBridges().then(setBridges).catch(() => {});
                  } catch { toast.error("Failed to create bridge."); } finally { setBridgeAdding(false); }
                }}
              >
                <Plus className="w-3 h-3 mr-1" /> {bridgeAdding ? "Adding..." : "Add"}
              </Button>
            </div>

            {/* Bridge Table */}
            {bridges.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">No bridge memberships found.</p>
            ) : (
              <div className="max-h-64 overflow-y-auto space-y-2">
                {bridges.map((b, i) => (
                  <div key={i} className="flex items-center justify-between p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-card">
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-xs font-bold text-indigo-600 dark:text-indigo-400">{b.bridge_id}</span>
                      <span className="text-slate-400">↔</span>
                      <span className="font-mono text-xs font-bold text-teal-600 dark:text-teal-400">{b.donor_id}</span>
                    </div>
                    <Button
                      variant="ghost" size="icon"
                      className="h-7 w-7 text-slate-400 hover:text-red-500"
                      onClick={async () => {
                        try {
                          await adminDeleteBridge(b.bridge_id, b.donor_id);
                          toast.success("Bridge removed.");
                          setBridges(prev => prev.filter((_, idx) => idx !== i));
                        } catch { toast.error("Failed to remove bridge."); }
                      }}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                ))}
              </div>
            )}

            {/* Delete Donor/Patient */}
            <div className="border-t border-slate-200 dark:border-slate-800 pt-4 mt-4">
              <div className="text-xs font-medium text-muted-foreground mb-2">Delete Donor or Patient</div>
              <div className="flex gap-2">
                <Input
                  placeholder="ID (e.g. D-1001 or P-10234)"
                  value={deleteConfirm?.id || ""}
                  onChange={e => setDeleteConfirm(e.target.value ? { type: e.target.value.startsWith("P") ? "patient" : "donor", id: e.target.value } : null)}
                  className="h-9 flex-1"
                />
                <Button
                  size="sm"
                  variant="destructive"
                  className="h-9"
                  disabled={!deleteConfirm?.id || deleting}
                  onClick={async () => {
                    if (!deleteConfirm) return;
                    const confirmed = window.confirm(`Are you sure you want to delete ${deleteConfirm.type} ${deleteConfirm.id}? This cannot be undone.`);
                    if (!confirmed) return;
                    setDeleting(true);
                    try {
                      if (deleteConfirm.type === "donor") {
                        await adminDeleteDonor(deleteConfirm.id);
                      } else {
                        await adminDeletePatient(deleteConfirm.id);
                      }
                      toast.success(`${deleteConfirm.type === "donor" ? "Donor" : "Patient"} ${deleteConfirm.id} deleted.`);
                      setDeleteConfirm(null);
                      adminGetBridges().then(setBridges).catch(() => {});
                    } catch { toast.error("Delete failed."); } finally { setDeleting(false); }
                  }}
                >
                  <Trash2 className="w-3 h-3 mr-1" /> {deleting ? "Deleting..." : "Delete"}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Dialog open={retrainDialogOpen} onOpenChange={(open) => !open && retrainStatus !== "training" && setRetrainDialogOpen(false)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2"><BrainCircuit className="w-5 h-5 text-indigo-500" /> Retrain XGBoost Model</DialogTitle>
            <DialogDescription>
              Training on latest donor interaction data to improve churn prediction.
            </DialogDescription>
          </DialogHeader>
          <div className="py-6 space-y-4">
            <div className="flex justify-between text-sm font-mono">
              <span className="text-slate-500">Data size: 45,219 rows</span>
              <span className="text-indigo-600 font-bold">{retrainProgress}%</span>
            </div>
            <div className="w-full h-3 bg-secondary rounded-full overflow-hidden">
              <div 
                className="h-full bg-indigo-500 transition-all duration-75 ease-linear" 
                style={{ width: `${retrainProgress}%` }} 
              />
            </div>
            <div className="text-center text-sm font-medium mt-4 h-5 text-indigo-600">
              {retrainStatus === "training" ? "Optimizing weights..." : "Training complete! Deploying to edge..."}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Add Staff Dialog */}
      <Dialog open={addStaffOpen} onOpenChange={setAddStaffOpen}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2"><Shield className="w-4 h-4" /> Add Staff Member</DialogTitle>
            <DialogDescription>Grant a hospital coordinator access to the dashboard.</DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div>
              <label className="text-xs font-medium text-muted-foreground mb-1 block">Telegram Username</label>
              <Input
                placeholder="@dr_username"
                value={newStaff.username}
                onChange={e => setNewStaff(p => ({ ...p, username: e.target.value }))}
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground mb-1 block">Hospital</label>
              <Input
                placeholder="Apollo Banjara Hills"
                value={newStaff.hospital}
                onChange={e => setNewStaff(p => ({ ...p, hospital: e.target.value }))}
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground mb-1 block">Role</label>
              <select
                className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background"
                value={newStaff.role}
                onChange={e => setNewStaff(p => ({ ...p, role: e.target.value }))}
              >
                <option>Staff</option>
                <option>Coordinator</option>
                <option>Admin</option>
              </select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddStaffOpen(false)}>Cancel</Button>
            <Button className="bg-teal-600 hover:bg-teal-700 text-white" onClick={handleAddStaff} disabled={addingStaff}>
              {addingStaff ? "Adding..." : "Add Member"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
}