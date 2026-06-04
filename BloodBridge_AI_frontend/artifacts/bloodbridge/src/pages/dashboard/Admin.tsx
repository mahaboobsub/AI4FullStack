import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { getSystemHealth, getAgentTraces, MOCK_STAFF, type ServiceHealth, type AgentTrace } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Activity, RefreshCcw, Server, Shield, Trash2, CheckCircle2, AlertTriangle, XCircle, ArrowRight, BrainCircuit } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { toast } from "sonner";
import { motion } from "framer-motion";

export default function Admin() {
  const [health, setHealth] = useState<ServiceHealth[]>([]);
  const [traces, setTraces] = useState<AgentTrace[]>([]);
  const [isRetraining, setIsRetraining] = useState(false);
  const [retrainDialogOpen, setRetrainDialogOpen] = useState(false);
  const [retrainProgress, setRetrainProgress] = useState(0);
  const [retrainStatus, setRetrainStatus] = useState<"idle"|"training"|"complete">("idle");

  useEffect(() => {
    getSystemHealth().then(setHealth);
    getAgentTraces().then(setTraces);
  }, []);

  const handleRetrainClick = () => {
    setRetrainDialogOpen(true);
    setRetrainStatus("training");
    setRetrainProgress(0);
    
    let current = 0;
    const interval = setInterval(() => {
      current += 5;
      setRetrainProgress(current);
      if (current >= 100) {
        clearInterval(interval);
        setRetrainStatus("complete");
        setTimeout(() => {
          setRetrainDialogOpen(false);
          toast.success("Model retraining job JOB-8472 queued successfully.");
        }, 1500);
      }
    }, 75);
  };

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
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
                    <span className="font-medium text-slate-700 dark:text-slate-300">Urgency Scorer (Groq)</span>
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
                  {MOCK_STAFF.map(staff => (
                    <div key={staff.username} className="flex items-center justify-between p-3 rounded-lg border border-transparent hover:border-slate-200 dark:hover:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors group">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-600 dark:text-slate-400">
                          {staff.username.replace('@', '').charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <div className="font-mono text-sm font-bold text-teal-700 dark:text-teal-400 mb-0.5">{staff.username}</div>
                          <div className="text-[10px] text-muted-foreground">{staff.hospital}</div>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <span className={`text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                          staff.role === 'Admin' ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400' :
                          staff.role === 'Coordinator' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                          'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
                        }`}>{staff.role}</span>
                        <Button variant="ghost" size="icon" className="h-5 w-5 text-slate-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"><Trash2 className="w-3 h-3" /></Button>
                      </div>
                    </div>
                  ))}
                  <Button variant="outline" className="w-full text-xs h-9 mt-4 border-dashed bg-transparent hover:bg-slate-50 dark:hover:bg-slate-900">Add Staff Member</Button>
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
    </DashboardLayout>
  );
}