import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { getGraphData, type GraphNode, type GraphLink } from "@/lib/api";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Phone, MessageSquare, ShieldAlert, Target, Info, Search, History, Dna } from "lucide-react";
import { toast } from "sonner";
import ForceGraph2D from "react-force-graph-2d";

const DEFAULT_REQUEST_ID = "REQ-TEST-B001";
const WS_URL = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL.replace(/^http/, "ws") + "/ws/emergencies"
  : `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/ws/emergencies`;

function formatAntigenPanel(panel?: Record<string, string>): string {
  if (!panel || Object.keys(panel).length === 0) return "Not scanned yet";
  return Object.entries(panel)
    .map(([k, v]) => {
      const val = String(v).toLowerCase();
      if (val.startsWith("pos")) return `${k}+`;
      if (val.startsWith("neg")) return `${k}−`;
      return `${k}:${v}`;
    })
    .join(", ");
}

export default function Graph() {
  const [data, setData] = useState<{ nodes: GraphNode[]; links: GraphLink[] }>({ nodes: [], links: [] });
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [hoverNode, setHoverNode] = useState<any | null>(null);
  const graphRef = useRef<any>(null);
  const [searchRequestId, setSearchRequestId] = useState(DEFAULT_REQUEST_ID);
  const [activeRequestId, setActiveRequestId] = useState(DEFAULT_REQUEST_ID);
  const [loading, setLoading] = useState(true);
  const [liveConnected, setLiveConnected] = useState(false);

  const fetchGraphData = useCallback((requestId?: string) => {
    const rid = requestId || DEFAULT_REQUEST_ID;
    setLoading(true);
    setActiveRequestId(rid);
    getGraphData(rid)
      .then((res) => {
        if (res?.nodes?.length > 0) {
          setData(res);
        } else {
          setData({ nodes: [], links: [] });
          toast.warning(`No graph data for ${rid}. Run seed_e2e_three_phones or create an emergency.`);
        }
      })
      .catch((err) => {
        console.error("Failed to load graph data", err);
        setData({ nodes: [], links: [] });
        toast.error("Graph API unavailable — is the backend running on :8000?");
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchGraphData(DEFAULT_REQUEST_ID);
  }, [fetchGraphData]);

  // Realtime: OCR scans + chain monitor updates refresh the graph
  useEffect(() => {
    let reconnectTimer: ReturnType<typeof setTimeout>;
    let mounted = true;

    const connect = () => {
      if (!mounted) return;
      try {
        const ws = new WebSocket(WS_URL);
        ws.onopen = () => setLiveConnected(true);
        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data as string);
            if (msg.type === "ocr_scan_complete") {
              toast.success(`OCR: ${msg.donor_id} — ${msg.blood_group || "?"} (${msg.antigen_summary || "antigens scanned"})`);
              fetchGraphData(activeRequestId);
            }
            if (msg.type === "chain_monitor_update" || msg.type === "chain_update" ||
                msg.type === "chain_repaired" || msg.type === "donor_confirmed" ||
                msg.type === "donor_declined" || msg.type === "emergency_created") {
              fetchGraphData(activeRequestId);
            }
            if (msg.type === "voice_call_active") {
              toast.info(`Voice call to ${msg.donor_id || "donor"}…`, { duration: 4000 });
            }
          } catch { /* ping/pong */ }
        };
        ws.onclose = () => {
          setLiveConnected(false);
          if (mounted) reconnectTimer = setTimeout(connect, 5000);
        };
        ws.onerror = () => ws.close();
      } catch {
        if (mounted) reconnectTimer = setTimeout(connect, 10000);
      }
    };
    connect();
    return () => { mounted = false; clearTimeout(reconnectTimer); };
  }, [activeRequestId, fetchGraphData]);

  const stats = useMemo(() => {
    const donors = data.nodes.filter(n => n.type === "donor");
    const patient = data.nodes.find(n => n.type === "patient");
    return {
      confirmed: donors.filter(d => d.status === "CONFIRMED").length,
      alerted: donors.filter(d => d.status === "ALERTED").length,
      pending: donors.filter(d => !d.status || d.status === "PENDING").length,
      patientId: patient?.id || activeRequestId,
      bloodType: patient?.blood_type || "—",
    };
  }, [data, activeRequestId]);

  const handleNodeClick = useCallback((node: any) => {
    if (node.type === "donor") setSelectedNode(node);
  }, []);

  const handleAction = (action: string) => {
    toast.success(`${action} initiated for ${selectedNode?.name}`);
    setSelectedNode(null);
  };

  const centerGraph = () => {
    graphRef.current?.zoomToFit(400, 50);
  };

  return (
    <DashboardLayout>
      <div className="relative w-full h-[calc(100vh-52px)] flex bg-[#0A0F1C] overflow-hidden">

        <div className="w-64 bg-[#0F1929]/95 backdrop-blur-xl border-r border-slate-800 p-5 flex flex-col z-20 shadow-2xl">
          <div className="flex items-center gap-2 mb-6">
            <NetworkIcon className="w-5 h-5 text-teal-500" />
            <h2 className="font-serif font-bold text-lg text-white">Blood Bridge Graph</h2>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 mb-6">
            <div className="text-[10px] uppercase font-bold text-slate-500 mb-1">Active Case</div>
            <div className="font-mono text-sm font-bold text-white mb-1">{stats.patientId} · {stats.bloodType}</div>
            <div className="flex items-center gap-2">
              <div className="inline-flex items-center gap-1.5 bg-red-500/10 text-red-400 text-[10px] font-bold px-2 py-0.5 rounded border border-red-500/20">
                <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" /> LIVE
              </div>
              {liveConnected && (
                <span className="text-[9px] text-emerald-400 font-mono">WS connected</span>
              )}
            </div>
          </div>

          <div className="space-y-4 mb-8">
            <div className="text-[10px] uppercase font-bold text-slate-500">Network Legend</div>
            <div className="space-y-3 text-xs text-slate-300">
              <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-emerald-500" /> <span>Confirmed Match</span></div>
              <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-amber-500" /> <span>AI Alerted</span></div>
              <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-red-500" /> <span>Declined</span></div>
              <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-slate-600" /> <span>Pending / Pool</span></div>
            </div>
          </div>

          <div className="mt-auto">
            <div className="grid grid-cols-2 gap-2 mb-4">
              <div className="bg-slate-900/50 border border-slate-800 rounded p-2 text-center">
                <div className="text-lg font-mono font-bold text-white">{data.nodes.length}</div>
                <div className="text-[9px] uppercase text-slate-500">Nodes</div>
              </div>
              <div className="bg-slate-900/50 border border-slate-800 rounded p-2 text-center">
                <div className="text-lg font-mono font-bold text-white">{data.links.length}</div>
                <div className="text-[9px] uppercase text-slate-500">Edges</div>
              </div>
            </div>
            <div className="flex justify-between text-[10px] font-mono text-slate-400 bg-slate-900/50 p-2 rounded border border-slate-800">
              <span className="text-emerald-400">{stats.confirmed} Conf</span>
              <span className="text-amber-400">{stats.alerted} Alrt</span>
              <span className="text-slate-500">{stats.pending} Pend</span>
            </div>
          </div>
        </div>

        <div className="flex-1 relative">
          <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-xl px-4 py-2 shadow-2xl flex items-center gap-4 w-[500px]">
            <Search className="w-4 h-4 text-slate-400" />
            <div className="h-4 w-px bg-slate-700" />
            <input
              type="text"
              className="bg-transparent border-0 text-slate-200 text-sm outline-none focus:ring-0 flex-1 placeholder-slate-500"
              placeholder="Search by request ID (e.g. REQ-TEST-B001)..."
              value={searchRequestId}
              onChange={(e) => setSearchRequestId(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") fetchGraphData(searchRequestId.trim() || undefined); }}
            />
            <button onClick={() => fetchGraphData(searchRequestId.trim() || undefined)}
              className="text-xs text-teal-400 hover:text-teal-300 font-medium whitespace-nowrap">
              Search
            </button>
          </div>

          {loading && (
            <div className="absolute inset-0 flex items-center justify-center z-10 bg-[#0A0F1C]/60">
              <div className="text-sm text-slate-400 font-mono flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-slate-600 border-t-teal-400 rounded-full animate-spin" />
                Loading graph data...
              </div>
            </div>
          )}

          {!loading && data.nodes.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center z-10">
              <div className="text-sm text-slate-500 font-mono text-center">
                No graph data for {activeRequestId}.<br />
                <span className="text-xs">Run: python -m data.seed_e2e_three_phones</span>
              </div>
            </div>
          )}

          {data.nodes.length > 0 && (
            <ForceGraph2D
              ref={graphRef}
              graphData={data}
              backgroundColor="#0A0F1C"
              nodeRelSize={6}
              linkDirectionalParticles={(link: any) => (link.status === "CONFIRMED" || hoverNode?.id === link.source?.id || hoverNode?.id === link.target?.id) ? 3 : 1}
              linkDirectionalParticleWidth={(link: any) => (link.status === "CONFIRMED" ? 4 : 2)}
              linkDirectionalParticleSpeed={0.005}
              linkColor={(link: any) => {
                const isHovered = hoverNode && (hoverNode.id === link.source?.id || hoverNode.id === link.target?.id);
                if (link.status === "CONFIRMED") return isHovered ? "rgba(16,185,129,0.9)" : "rgba(16,185,129,0.6)";
                if (link.status === "ALERTED") return isHovered ? "rgba(245,158,11,0.8)" : "rgba(245,158,11,0.4)";
                if (link.status === "DECLINED") return isHovered ? "rgba(239,68,68,0.7)" : "rgba(239,68,68,0.3)";
                return isHovered ? "rgba(148,163,184,0.8)" : "rgba(51,65,85,0.4)";
              }}
              linkWidth={(link: any) => {
                const isHovered = hoverNode && (hoverNode.id === link.source?.id || hoverNode.id === link.target?.id);
                const baseWidth = link.antigen_score ? link.antigen_score * 3 : 1;
                return isHovered ? baseWidth * 1.5 : baseWidth;
              }}
              nodeCanvasObject={(node: any, ctx, globalScale) => {
                const label = node.name;
                const fontSize = 10 / globalScale;
                const isHovered = hoverNode?.id === node.id;
                const isDimmed = hoverNode && !isHovered &&
                  !data.links.some((l: any) => (l.source?.id === hoverNode.id && l.target?.id === node.id) || (l.target?.id === hoverNode.id && l.source?.id === node.id));
                ctx.globalAlpha = isDimmed ? 0.3 : 1;

                if (node.type === "patient") {
                  ctx.fillStyle = "#EF4444";
                  ctx.beginPath();
                  ctx.arc(node.x, node.y, isHovered ? 12 : 10, 0, 2 * Math.PI, false);
                  ctx.fill();
                  ctx.fillStyle = "#ffffff";
                  ctx.font = `bold ${12 / globalScale}px monospace`;
                  ctx.textAlign = "center";
                  ctx.textBaseline = "middle";
                  ctx.fillText("P", node.x, node.y);
                } else if (node.type === "hospital") {
                  ctx.fillStyle = "#475569";
                  ctx.fillRect(node.x - 8, node.y - 8, 16, 16);
                  ctx.fillStyle = "#ffffff";
                  ctx.font = `bold ${10 / globalScale}px monospace`;
                  ctx.textAlign = "center";
                  ctx.textBaseline = "middle";
                  ctx.fillText("H", node.x, node.y);
                } else {
                  ctx.fillStyle = node.status === "CONFIRMED" ? "#10B981" : node.status === "ALERTED" ? "#FBBF24" : node.status === "DECLINED" ? "#EF4444" : "#475569";
                  ctx.beginPath();
                  ctx.arc(node.x, node.y, isHovered ? 8 : 6, 0, 2 * Math.PI, false);
                  ctx.fill();
                  ctx.fillStyle = "#ffffff";
                  ctx.font = `bold ${8 / globalScale}px sans-serif`;
                  ctx.textAlign = "center";
                  ctx.textBaseline = "middle";
                  ctx.fillText(node.name?.charAt(0) || "?", node.x, node.y);
                }

                if (isHovered || globalScale > 1.5) {
                  ctx.font = `${fontSize}px Sans-Serif`;
                  ctx.textAlign = "center";
                  ctx.textBaseline = "top";
                  const textWidth = ctx.measureText(label || "Unknown").width;
                  ctx.fillStyle = "rgba(15, 23, 42, 0.8)";
                  ctx.fillRect(node.x - textWidth / 2 - 2, node.y + 12 - 1, textWidth + 4, fontSize * 1.4);
                  ctx.fillStyle = isHovered ? "#ffffff" : "rgba(255, 255, 255, 0.8)";
                  ctx.fillText(label || "Unknown", node.x, node.y + 12);
                }
                ctx.globalAlpha = 1;
              }}
              onNodeHover={(node: any) => { setHoverNode(node || null); document.body.style.cursor = node ? "pointer" : "default"; }}
              onNodeClick={handleNodeClick}
              onEngineStop={centerGraph}
            />
          )}

          <button onClick={centerGraph}
            className="absolute bottom-6 right-6 z-10 w-10 h-10 bg-slate-800 border border-slate-700 rounded-full flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-700 shadow-lg transition-colors"
            title="Recenter Graph">
            <Target className="w-5 h-5" />
          </button>
        </div>

        <Sheet open={!!selectedNode} onOpenChange={() => setSelectedNode(null)}>
          <SheetContent side="right" className="w-[380px] bg-[#0F172A]/95 backdrop-blur-xl border-l-slate-800 text-slate-200 p-0 flex flex-col">
            {selectedNode && (
              <>
                <div className="p-6 pb-0 flex-1 overflow-y-auto">
                  <SheetHeader className="mb-6">
                    <SheetTitle className="text-2xl font-serif text-white">{selectedNode.name}</SheetTitle>
                    <SheetDescription className="font-mono text-xs">{selectedNode.id} · {selectedNode.blood_type}</SheetDescription>
                  </SheetHeader>

                  <div className="space-y-6">
                    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
                      <div className="text-[10px] text-slate-500 uppercase tracking-widest font-bold mb-2 flex items-center gap-2">
                        <Dna className="w-3 h-3" /> OCR Antigen Panel
                      </div>
                      <p className="text-sm text-teal-300 font-mono leading-relaxed">
                        {formatAntigenPanel(selectedNode.antigen_panel)}
                      </p>
                      {selectedNode.kell_negative && (
                        <p className="text-[10px] text-emerald-400 mt-2">Kell-negative confirmed</p>
                      )}
                    </div>

                    <div>
                      <div className="text-[10px] text-slate-500 uppercase tracking-widest font-bold mb-4">Compatibility</div>
                      <div className="flex justify-center relative h-20 overflow-hidden">
                        <div className="absolute bottom-2 flex flex-col items-center">
                          <span className="text-2xl font-mono font-bold text-white">{Math.round((selectedNode.antigen_score || 0) * 100)}%</span>
                          <span className="text-[10px] text-slate-400">Match Score</span>
                        </div>
                      </div>
                    </div>

                    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
                      <div className="flex justify-between items-end mb-2">
                        <div className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Churn Risk</div>
                        <span className="font-mono text-sm font-bold">{Math.round((selectedNode.churn_score || 0) * 100)}%</span>
                      </div>
                      <div className="flex-1 bg-slate-800 h-2 rounded-full overflow-hidden">
                        <div className={`h-full ${(selectedNode.churn_score || 0) > 0.7 ? "bg-red-500" : (selectedNode.churn_score || 0) > 0.4 ? "bg-amber-500" : "bg-emerald-500"}`}
                          style={{ width: `${(selectedNode.churn_score || 0) * 100}%` }} />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="p-6 bg-slate-900 border-t border-slate-800 grid grid-cols-3 gap-2">
                  <Button onClick={() => handleAction("Voice Call")} className="bg-[#6B21A8] hover:bg-[#581C87] text-white flex-col h-14 gap-1 rounded-xl">
                    <Phone className="w-4 h-4" /> <span className="text-[10px]">Voice</span>
                  </Button>
                  <Button onClick={() => handleAction("AI Message")} className="bg-teal-600 hover:bg-teal-700 text-white flex-col h-14 gap-1 rounded-xl">
                    <MessageSquare className="w-4 h-4" /> <span className="text-[10px]">AI Msg</span>
                  </Button>
                  <Button onClick={() => handleAction("View Full Profile")} className="bg-slate-800 hover:bg-slate-700 text-white flex-col h-14 gap-1 rounded-xl">
                    <Info className="w-4 h-4" /> <span className="text-[10px]">Profile</span>
                  </Button>
                </div>
              </>
            )}
          </SheetContent>
        </Sheet>
      </div>
    </DashboardLayout>
  );
}

function NetworkIcon(props: any) {
  return (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="16" y="16" width="6" height="6" rx="1" />
      <rect x="2" y="16" width="6" height="6" rx="1" />
      <rect x="9" y="2" width="6" height="6" rx="1" />
      <path d="M5 16v-3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3" />
      <path d="M12 12V8" />
    </svg>
  );
}
