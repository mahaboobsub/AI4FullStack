import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { getAnalytics, getDonors, triggerVoiceCall, triggerOutreach, type EngagementMetrics, type Donor } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer, CartesianGrid, LabelList } from "recharts";
import { MessageSquare, Phone, Activity, HeartPulse, ArrowUpRight, ArrowDownRight, Users, Play } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { motion } from "framer-motion";

export default function Donors() {
  const [metrics, setMetrics] = useState<EngagementMetrics | null>(null);
  const [donors, setDonors] = useState<Donor[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    getAnalytics().then(setMetrics);
    getDonors().then(setDonors);
  }, []);

  const handleRunBatch = () => {
    setIsProcessing(true);
    setTimeout(() => {
      setIsProcessing(false);
      toast.success("AI Outreach Batch completed. 12 at-risk donors contacted.");
    }, 1500);
  };

  const handleVoiceCall = async (donor: Donor) => {
    toast.info(`Initiating voice call to ${donor.name}...`);
    try {
      const result = await triggerVoiceCall(donor.donor_id);
      if (result.status === "INITIATED") {
        toast.success(`Voice call initiated — SID: ${result.callSid}`);
      } else if (result.status === "QUEUED") {
        toast.warning(`Call queued — ${result.reason}. TRAI safe hours: 8 AM – 9 PM IST.`);
      } else {
        toast.error(`Call failed: ${result.message}`);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      toast.error(`Failed to initiate voice call to ${donor.name}: ${message}`);
    }
  };

  const handleOutreach = async (donor: Donor) => {
    toast.info(`Sending Telegram message to ${donor.name}...`);
    try {
      const result = await triggerOutreach(donor.donor_id);
      toast.success(`Message sent — ID: ${result.messageId}`);
    } catch {
      toast.error(`Failed to send message to ${donor.name}.`);
    }
  };

  if (!metrics) return <DashboardLayout><div className="p-8 text-center text-muted-foreground">Loading engagement data...</div></DashboardLayout>;

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Donor Engagement</h1>
            <p className="text-sm text-muted-foreground mt-1">Predictive churn modeling & retention campaigns</p>
          </div>
          <Button onClick={handleRunBatch} disabled={isProcessing} className="bg-teal-600 hover:bg-teal-700 text-white shadow-sm gap-2">
            <Activity className="w-4 h-4" /> {isProcessing ? "Running Batch..." : "Run AI Outreach Batch"}
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-gradient-to-br from-teal-50 to-teal-100/50 dark:from-teal-950/20 dark:to-teal-900/10 border-teal-200 dark:border-teal-900/50 relative overflow-hidden">
            <CardContent className="p-5 flex items-center justify-between z-10">
              <div className="flex gap-4 items-center">
                <div className="relative w-16 h-16 flex items-center justify-center shrink-0">
                  <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="40" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-teal-200 dark:text-teal-950" />
                    <circle cx="50" cy="50" r="40" stroke="currentColor" strokeWidth="8" fill="transparent" strokeDasharray="251.2" strokeDashoffset={251.2 - (251.2 * metrics.active_pct / 100)} className="text-teal-600 dark:text-teal-500 transition-all duration-1000 ease-out" />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-sm font-bold text-teal-700 dark:text-teal-400">{metrics.active_pct}%</span>
                  </div>
                </div>
                <div>
                  <p className="text-sm text-teal-800/70 dark:text-teal-400/70 font-medium">Active Donors</p>
                  <div className="flex items-center gap-2">
                    <p className="text-3xl font-bold text-teal-900 dark:text-teal-100">{metrics.active_donors}</p>
                    <span className="text-xs font-medium text-teal-600 dark:text-teal-500 flex items-center"><ArrowUpRight className="w-3 h-3" /> 4%</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-red-50 to-red-100/50 dark:from-red-950/20 dark:to-red-900/10 border-red-200 dark:border-red-900/50">
            <CardContent className="p-5">
              <div className="flex justify-between items-start mb-2">
                <div className="w-8 h-8 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                  <Activity className="w-4 h-4 text-red-600 dark:text-red-400" />
                </div>
                <div className="flex gap-0.5 items-end h-6">
                  {[2,3,4,6,8].map((h, i) => <div key={i} className="w-1.5 bg-red-400 dark:bg-red-500/50 rounded-t-sm" style={{height: `${h*3}px`}} />)}
                </div>
              </div>
              <p className="text-sm text-red-800/70 dark:text-red-400/70 font-medium">At-Risk Donors</p>
              <div className="flex items-center gap-2 mt-1">
                <p className="text-3xl font-bold text-red-900 dark:text-red-100">{metrics.at_risk_count}</p>
                <span className="text-xs font-medium text-red-600 dark:text-red-500 flex items-center"><ArrowUpRight className="w-3 h-3" /> 12</span>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-amber-50 to-amber-100/50 dark:from-amber-950/20 dark:to-amber-900/10 border-amber-200 dark:border-amber-900/50">
            <CardContent className="p-5">
              <div className="flex justify-between items-start mb-2">
                <div className="w-8 h-8 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                  <MessageSquare className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                </div>
                <div className="flex gap-0.5 items-end h-6">
                  {[8,7,7,6,7].map((h, i) => <div key={i} className="w-1.5 bg-amber-400 dark:bg-amber-500/50 rounded-t-sm" style={{height: `${h*3}px`}} />)}
                </div>
              </div>
              <p className="text-sm text-amber-800/70 dark:text-amber-400/70 font-medium">Avg Response Rate</p>
              <div className="flex items-center gap-2 mt-1">
                <p className="text-3xl font-bold text-amber-900 dark:text-amber-100">{metrics.avg_response_rate}%</p>
                <span className="text-xs font-medium text-amber-600 dark:text-amber-500 flex items-center"><ArrowDownRight className="w-3 h-3" /> 2%</span>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100/50 dark:from-emerald-950/20 dark:to-emerald-900/10 border-emerald-200 dark:border-emerald-900/50">
            <CardContent className="p-5">
              <div className="flex justify-between items-start mb-2">
                <div className="w-8 h-8 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
                  <HeartPulse className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                </div>
                <div className="flex gap-0.5 items-end h-6">
                  {[3,4,6,5,8].map((h, i) => <div key={i} className="w-1.5 bg-emerald-400 dark:bg-emerald-500/50 rounded-t-sm" style={{height: `${h*3}px`}} />)}
                </div>
              </div>
              <p className="text-sm text-emerald-800/70 dark:text-emerald-400/70 font-medium">Donated This Month</p>
              <div className="flex items-center gap-2 mt-1">
                <p className="text-3xl font-bold text-emerald-900 dark:text-emerald-100">{metrics.donated_this_month}</p>
                <span className="text-xs font-medium text-emerald-600 dark:text-emerald-500 flex items-center"><ArrowUpRight className="w-3 h-3" /> 18%</span>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader className="pb-4">
              <CardTitle className="text-base font-semibold">Active Donor Trend (30d)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[250px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={metrics.trend} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorActive" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#0D9488" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#0D9488" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="opacity-10" />
                    <XAxis dataKey="date" tick={{fontSize: 11, fill: 'currentColor', opacity: 0.5}} tickLine={false} axisLine={false} />
                    <YAxis domain={['dataMin - 5', 'dataMax + 5']} tick={{fontSize: 11, fill: 'currentColor', opacity: 0.5}} tickLine={false} axisLine={false} />
                    <RechartsTooltip contentStyle={{ borderRadius: '8px', fontSize: '12px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(15,23,42,0.9)', color: '#fff' }} />
                    <Area type="monotone" dataKey="active_pct" name="Active %" stroke="#0D9488" strokeWidth={3} fillOpacity={1} fill="url(#colorActive)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-4">
              <CardTitle className="text-base font-semibold">Donations by City</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[250px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={metrics.by_city} margin={{ top: 20, right: 0, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="opacity-10" />
                    <XAxis dataKey="city" tick={{fontSize: 11, fill: 'currentColor', opacity: 0.5}} tickLine={false} axisLine={false} />
                    <YAxis tick={{fontSize: 11, fill: 'currentColor', opacity: 0.5}} tickLine={false} axisLine={false} />
                    <RechartsTooltip cursor={{fill: 'currentColor', opacity: 0.05}} contentStyle={{ borderRadius: '8px', fontSize: '12px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(15,23,42,0.9)', color: '#fff' }} />
                    <Bar dataKey="donations" name="Donations" fill="#0D9488" radius={[4, 4, 0, 0]}>
                      <LabelList dataKey="donations" position="top" style={{ fontSize: '10px', fill: 'currentColor', opacity: 0.7 }} />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Donor Roster (At-Risk Prioritized)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border overflow-hidden">
              <Table>
                <TableHeader className="bg-muted/50">
                  <TableRow>
                    <TableHead>Donor</TableHead>
                    <TableHead>Blood Type</TableHead>
                    <TableHead>Last Donation</TableHead>
                    <TableHead className="w-[200px]">Churn Score (XGBoost)</TableHead>
                    <TableHead>Risk Tier</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {donors.map((donor, idx) => (
                    <TableRow key={donor.donor_id} className="hover:bg-muted/30">
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-3">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold relative ${
                            donor.churn_risk === 'CRITICAL' ? 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-400' :
                            donor.churn_risk === 'HIGH' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-400' :
                            'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
                          }`}>
                            {donor.name.charAt(0)}
                            <div className="absolute -bottom-1 -right-1 bg-background rounded-full p-0.5">
                              <span className="flex items-center justify-center w-4 h-4 bg-slate-200 dark:bg-slate-700 rounded-full text-[8px] font-mono leading-none">
                                {donor.blood_type.replace(/[^+-]/g, '')}
                              </span>
                            </div>
                          </div>
                          <div className="flex flex-col">
                            <span>{donor.name}</span>
                            <span className="text-[10px] text-muted-foreground font-mono">{donor.donor_id}</span>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className="font-mono text-xs px-2.5 py-1 bg-slate-100 dark:bg-slate-800 rounded font-bold border border-slate-200 dark:border-slate-700">{donor.blood_type}</span>
                      </TableCell>
                      <TableCell>
                        <span className={`text-sm ${donor.last_donation_days > 90 ? 'text-red-600 dark:text-red-400 font-medium' : donor.last_donation_days > 60 ? 'text-amber-600 dark:text-amber-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                          {donor.last_donation_days} days ago
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
                            <motion.div 
                              initial={{ width: 0 }}
                              animate={{ width: `${donor.churn_score * 100}%` }}
                              transition={{ duration: 1, delay: idx * 0.1 }}
                              className={`h-full ${donor.churn_score > 0.7 ? 'bg-red-500' : donor.churn_score > 0.4 ? 'bg-amber-500' : 'bg-emerald-500'}`} 
                            />
                          </div>
                          <span className="text-xs font-mono w-8">{donor.churn_score.toFixed(2)}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                          donor.churn_risk === 'CRITICAL' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 border border-red-200 dark:border-red-800' :
                          donor.churn_risk === 'HIGH' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 border border-amber-200 dark:border-amber-800' :
                          donor.churn_risk === 'MEDIUM' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400 border border-yellow-200 dark:border-yellow-800' :
                          'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800'
                        }`}>
                          {donor.churn_risk === 'CRITICAL' && <div className="w-1 h-1 rounded-full bg-red-500 animate-pulse mr-1.5" />}
                          {donor.churn_risk}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-teal-600 hover:text-teal-700 hover:bg-teal-50 dark:hover:bg-teal-900/20 rounded-full" title="Send Telegram Message" onClick={() => handleOutreach(donor)}><MessageSquare className="w-4 h-4" /></Button>
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-500 hover:text-slate-700 dark:hover:bg-slate-800 rounded-full" title="Initiate Voice Call" onClick={() => handleVoiceCall(donor)}><Phone className="w-4 h-4" /></Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* AI Outreach Campaigns */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold tracking-tight">AI Outreach Campaigns</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-card border rounded-xl p-5 shadow-sm">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="font-bold text-base mb-1">At-Risk Reconnect</h3>
                  <div className="text-xs text-muted-foreground">Targeting high-churn risk donors</div>
                </div>
                <div className="bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border border-blue-200 dark:border-blue-800">
                  Active
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 mb-4 text-sm">
                <div>
                  <div className="text-muted-foreground text-xs">Donors Targeted</div>
                  <div className="font-semibold font-mono">47</div>
                </div>
                <div>
                  <div className="text-muted-foreground text-xs">Open Rate</div>
                  <div className="font-semibold font-mono text-teal-600 dark:text-teal-400">71%</div>
                </div>
              </div>
              <div className="text-[10px] text-muted-foreground mb-4">Last run: 2 days ago</div>
              <Button className="w-full bg-teal-600 hover:bg-teal-700 text-white gap-2" size="sm">
                <Play className="w-3 h-3" /> Run Campaign Now
              </Button>
            </div>

            <div className="bg-card border rounded-xl p-5 shadow-sm">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="font-bold text-base mb-1">Monthly Reminder</h3>
                  <div className="text-xs text-muted-foreground">Standard 90-day eligibility nudge</div>
                </div>
                <div className="bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border border-emerald-200 dark:border-emerald-800">
                  Completed
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 mb-4 text-sm">
                <div>
                  <div className="text-muted-foreground text-xs">Donors Targeted</div>
                  <div className="font-semibold font-mono">200</div>
                </div>
                <div>
                  <div className="text-muted-foreground text-xs">Open Rate</div>
                  <div className="font-semibold font-mono text-teal-600 dark:text-teal-400">85%</div>
                </div>
              </div>
              <div className="text-[10px] text-muted-foreground mb-4">Last run: 1 day ago</div>
              <Button variant="outline" className="w-full gap-2" size="sm">
                View Results
              </Button>
            </div>

            <div className="bg-card border rounded-xl p-5 shadow-sm">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="font-bold text-base mb-1">Blood Group Alert</h3>
                  <div className="text-xs text-muted-foreground">Urgent regional shortage notification</div>
                </div>
                <div className="bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border border-slate-200 dark:border-slate-700">
                  Idle
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 mb-4 text-sm">
                <div>
                  <div className="text-muted-foreground text-xs">Donors Targeted</div>
                  <div className="font-semibold font-mono">-</div>
                </div>
                <div>
                  <div className="text-muted-foreground text-xs">Open Rate</div>
                  <div className="font-semibold font-mono">-</div>
                </div>
              </div>
              <div className="text-[10px] text-muted-foreground mb-4">On-demand campaign</div>
              <Button variant="outline" className="w-full gap-2 text-muted-foreground hover:text-foreground" size="sm">
                Configure
              </Button>
            </div>
          </div>
        </div>

      </div>
    </DashboardLayout>
  );
}