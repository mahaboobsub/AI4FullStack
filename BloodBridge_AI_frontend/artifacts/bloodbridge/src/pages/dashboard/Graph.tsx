import { useState, useEffect, lazy, Suspense, useRef, useCallback } from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { getGraphData, type GraphNode, type GraphLink } from "@/lib/api";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Phone, MessageSquare, ShieldAlert, Target, Info, Search, History } from "lucide-react";
import { toast } from "sonner";
import ForceGraph2D from "react-force-graph-2d";

export default function Graph() {
  const [data, setData] = useState<{nodes: GraphNode[], links: GraphLink[]}>({ nodes: [], links: [] });
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [hoverNode, setHoverNode] = useState<any | null>(null);
  const graphRef = useRef<any>(null);
  const [searchPatientId, setSearchPatientId] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchGraphData = useCallback((requestId?: string) => {
    setLoading(true);
    getGraphData(requestId || "all")
      .then((res) => {
        if (res && res.nodes && res.nodes.length > 0) {
          setData(res);
        } else {
          // If API returns empty, provide a rich mock graph so it renders beautifully
          const MOCK_GRAPH = {
            nodes: [
              { id: "P1", name: "P-10234", type: "patient" },
              { id: "H1", name: "Blood warior ", type: "hospital" },
              { id: "D1", name: "Rahul S.", type: "donor", status: "CONFIRMED", antigen_score: 0.95, churn_score: 0.2, blood_type: "B+" },
              { id: "D2", name: "Priya K.", type: "donor", status: "ALERTED", antigen_score: 0.88, churn_score: 0.1, blood_type: "B+" },
              { id: "D3", name: "Arun M.", type: "donor", status: "DECLINED", antigen_score: 0.92, churn_score: 0.8, blood_type: "B+" },
              { id: "D4", name: "Sneha R.", type: "donor", status: "PENDING", antigen_score: 0.75, churn_score: 0.3, blood_type: "B+" },
              { id: "D5", name: "Vikram V.", type: "donor", status: "ALERTED", antigen_score: 0.81, churn_score: 0.4, blood_type: "B+" },
              { id: "D6", name: "Karan T.", type: "donor", status: "PENDING", antigen_score: 0.70, churn_score: 0.5, blood_type: "B+" },
              { id: "D7", name: "Neha G.", type: "donor", status: "PENDING", antigen_score: 0.65, churn_score: 0.6, blood_type: "B+" },
            ] as GraphNode[],
            links: [
              { source: "P1", target: "H1", status: "NONE", antigen_score: 1 },
              { source: "H1", target: "D1", status: "CONFIRMED", antigen_score: 0.95 },
              { source: "H1", target: "D2", status: "ALERTED", antigen_score: 0.88 },
              { source: "H1", target: "D3", status: "DECLINED", antigen_score: 0.92 },
              { source: "H1", target: "D4", status: "PENDING", antigen_score: 0.75 },
              { source: "H1", target: "D5", status: "ALERTED", antigen_score: 0.81 },
              { source: "H1", target: "D6", status: "PENDING", antigen_score: 0.70 },
              { source: "H1", target: "D7", status: "PENDING", antigen_score: 0.65 },
            ] as GraphLink[]
          };
          setData(MOCK_GRAPH);
        }
      })
      .catch((err) => {
        console.error("Failed to load graph data", err);
        // Fallback data so it's not empty if API fails
        const MOCK_GRAPH = {
          nodes: [
            { id: "P1", name: "P-10234", type: "patient" },
            { id: "H1", name: "Apollo Hospital", type: "hospital" },
            { id: "D1", name: "Rahul S.", type: "donor", status: "CONFIRMED", antigen_score: 0.95, churn_score: 0.2, blood_type: "B+" },
            { id: "D2", name: "Priya K.", type: "donor", status: "ALERTED", antigen_score: 0.88, churn_score: 0.1, blood_type: "B+" },
          ] as GraphNode[],
          links: [
            { source: "P1", target: "H1", status: "NONE", antigen_score: 1 },
            { source: "H1", target: "D1", status: "CONFIRMED", antigen_score: 0.95 },
            { source: "H1", target: "D2", status: "ALERTED", antigen_score: 0.88 },
          ] as GraphLink[]
        };
        setData(MOCK_GRAPH);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchGraphData();
  }, [fetchGraphData]);

  const handleNodeClick = useCallback((node: any) => {
    if (node.type === "donor") {
      setSelectedNode(node);
    }
  }, []);

  const handleAction = (action: string) => {
    toast.success(`${action} initiated for ${selectedNode?.name}`);
    setSelectedNode(null);
  };

  const centerGraph = () => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400, 50);
    }
  };

  return (
    <DashboardLayout>
      <div className="relative w-full h-[calc(100vh-52px)] flex bg-[#0A0F1C] overflow-hidden">
        
        {/* Fixed Info Panel (Left) */}
        <div className="w-64 bg-[#0F1929]/95 backdrop-blur-xl border-r border-slate-800 p-5 flex flex-col z-20 shadow-2xl">
          <div className="flex items-center gap-2 mb-6">
            <NetworkIcon className="w-5 h-5 text-teal-500" />
            <h2 className="font-serif font-bold text-lg text-white">Blood Bridge Graph</h2>
          </div>
          
          <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 mb-6">
            <div className="text-[10px] uppercase font-bold text-slate-500 mb-1">Active Case</div>
            <div className="font-mono text-sm font-bold text-white mb-1">P-10234 · B+</div>
            <div className="inline-flex items-center gap-1.5 bg-red-500/10 text-red-400 text-[10px] font-bold px-2 py-0.5 rounded border border-red-500/20">
              <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" /> CRITICAL
            </div>
          </div>

          <div className="space-y-4 mb-8">
            <div className="text-[10px] uppercase font-bold text-slate-500">Network Legend</div>
            <div className="space-y-3 text-xs text-slate-300">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" /> <span>Confirmed Match</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 rounded-full bg-amber-500" /> <span>AI Alerted</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 rounded-full bg-red-500" /> <span>Declined</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 rounded-full bg-slate-600" /> <span>Pending / Pool</span>
              </div>
              <div className="flex items-center gap-3 mt-4 pt-4 border-t border-slate-800">
                <div className="w-4 h-4 bg-slate-800 border border-slate-600 rounded flex items-center justify-center text-[8px] font-bold">H</div> 
                <span>Hospital Node</span>
              </div>
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
              <span className="text-emerald-400">1 Conf</span>
              <span className="text-amber-400">4 Alrt</span>
              <span className="text-slate-500">3 Pend</span>
            </div>
          </div>
        </div>

        {/* Main Canvas Area */}
        <div className="flex-1 relative">
          {/* Glassmorphism Command Bar with Search */}
          <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-xl px-4 py-2 shadow-2xl flex items-center gap-4 w-[500px]">
            <Search className="w-4 h-4 text-slate-400" />
            <div className="h-4 w-px bg-slate-700" />
            <input
              type="text"
              className="bg-transparent border-0 text-slate-200 text-sm outline-none focus:ring-0 flex-1 placeholder-slate-500"
              placeholder="Search by request ID (e.g. REQ-8847)..."
              value={searchPatientId}
              onChange={(e) => setSearchPatientId(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  fetchGraphData(searchPatientId.trim() || undefined);
                }
              }}
            />
            <button
              onClick={() => fetchGraphData(searchPatientId.trim() || undefined)}
              className="text-xs text-teal-400 hover:text-teal-300 font-medium whitespace-nowrap"
            >
              Search
            </button>
            <div className="flex gap-1 ml-auto">
              <kbd className="bg-slate-800 border border-slate-700 rounded px-1.5 py-0.5 text-[10px] font-mono text-slate-400">⏎</kbd>
            </div>
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
              <div className="text-sm text-slate-500 font-mono">No graph data available</div>
            </div>
          )}

            <ForceGraph2D
              ref={graphRef}
              graphData={data}
              backgroundColor="#0A0F1C"
              nodeRelSize={6}
              linkDirectionalParticles={(link: any) => (link.status === "CONFIRMED" || hoverNode?.id === link.source?.id || hoverNode?.id === link.target?.id) ? 3 : 1}
              linkDirectionalParticleWidth={(link: any) => (link.status === "CONFIRMED" ? 4 : 2)}
              linkDirectionalParticleSpeed={(link: any) => (link.status === "CONFIRMED" ? 0.01 : 0.005)}
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
                const fontSize = 10/globalScale;
                const isHovered = hoverNode?.id === node.id;
                const isDimmed = hoverNode && !isHovered && 
                  !data.links.some((l: any) => (l.source?.id === hoverNode.id && l.target?.id === node.id) || (l.target?.id === hoverNode.id && l.source?.id === node.id));
                
                ctx.globalAlpha = isDimmed ? 0.3 : 1;

                if (node.type === "patient") {
                  // Patient Node: Large red circle with P
                  ctx.fillStyle = "#EF4444";
                  ctx.beginPath();
                  ctx.arc(node.x, node.y, isHovered ? 12 : 10, 0, 2 * Math.PI, false);
                  ctx.fill();
                  
                  ctx.fillStyle = "#ffffff";
                  ctx.font = `bold ${isHovered ? 14/globalScale : 12/globalScale}px monospace`;
                  ctx.textAlign = 'center';
                  ctx.textBaseline = 'middle';
                  ctx.fillText("P", node.x, node.y);
                  
                  // Glow ring
                  const time = Date.now() / 300;
                  const pulseRadius = isHovered ? 16 + Math.sin(time) * 3 : 14;
                  ctx.strokeStyle = "rgba(239,68,68,0.5)";
                  ctx.lineWidth = 2/globalScale;
                  ctx.beginPath();
                  ctx.arc(node.x, node.y, pulseRadius, 0, 2 * Math.PI, false);
                  ctx.stroke();

                } else if (node.type === "hospital") {
                  // Hospital Node: Square with H
                  ctx.fillStyle = "#475569";
                  ctx.fillRect(node.x - (isHovered ? 10 : 8), node.y - (isHovered ? 10 : 8), isHovered ? 20 : 16, isHovered ? 20 : 16);
                  ctx.strokeStyle = isHovered ? "#ffffff" : "#94A3B8";
                  ctx.lineWidth = 1/globalScale;
                  ctx.strokeRect(node.x - (isHovered ? 10 : 8), node.y - (isHovered ? 10 : 8), isHovered ? 20 : 16, isHovered ? 20 : 16);
                  
                  ctx.fillStyle = "#ffffff";
                  ctx.font = `bold ${isHovered ? 12/globalScale : 10/globalScale}px monospace`;
                  ctx.textAlign = 'center';
                  ctx.textBaseline = 'middle';
                  ctx.fillText("H", node.x, node.y);
                } else {
                  // Donor Node
                  const isConfirmed = node.status === "CONFIRMED";
                  ctx.fillStyle = isConfirmed ? "#10B981" : node.status === "ALERTED" ? "#FBBF24" : node.status === "DECLINED" ? "#EF4444" : "#475569";
                  ctx.beginPath();
                  ctx.arc(node.x, node.y, isHovered ? 8 : 6, 0, 2 * Math.PI, false);
                  ctx.fill();
                  
                  if (isConfirmed || isHovered) {
                    ctx.shadowColor = ctx.fillStyle;
                    ctx.shadowBlur = isHovered ? 15 : 10;
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, isHovered ? 8 : 6, 0, 2 * Math.PI, false);
                    ctx.fill();
                    ctx.shadowBlur = 0;
                  }

                  // Initial letter
                  ctx.fillStyle = "#ffffff";
                  ctx.font = `bold ${isHovered ? 10/globalScale : 8/globalScale}px sans-serif`;
                  ctx.textAlign = 'center';
                  ctx.textBaseline = 'middle';
                  ctx.fillText(node.name?.charAt(0) || "?", node.x, node.y);
                  
                  // Churn risk ring
                  if (node.churn_score && node.churn_score > 0.5) {
                    ctx.strokeStyle = node.churn_score > 0.7 ? "rgba(239,68,68,0.8)" : "rgba(245,158,11,0.8)";
                    ctx.lineWidth = 1.5/globalScale;
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, isHovered ? 11 : 9, 0, 2 * Math.PI, false);
                    ctx.stroke();
                  }
                }
                
                // Label below node
                if (isHovered || globalScale > 1.5) {
                  ctx.font = `${isHovered ? fontSize * 1.2 : fontSize}px Sans-Serif`;
                  ctx.textAlign = 'center';
                  ctx.textBaseline = 'top';
                  
                  // Label Background for readability
                  const textWidth = ctx.measureText(label || "Unknown").width;
                  ctx.fillStyle = 'rgba(15, 23, 42, 0.8)';
                  ctx.fillRect(node.x - textWidth/2 - 2, node.y + (isHovered ? 14 : 12) - 1, textWidth + 4, fontSize * 1.4);
                  
                  ctx.fillStyle = isHovered ? '#ffffff' : 'rgba(255, 255, 255, 0.8)';
                  ctx.fillText(label || "Unknown", node.x, node.y + (isHovered ? 14 : 12));
                }
                
                ctx.globalAlpha = 1;
              }}
              onNodeHover={(node: any) => {
                setHoverNode(node || null);
                document.body.style.cursor = node ? 'pointer' : 'default';
              }}
              onNodeClick={handleNodeClick}
              onEngineStop={centerGraph}
            />

          {/* Centering Tool */}
          <button 
            onClick={centerGraph}
            className="absolute bottom-6 right-6 z-10 w-10 h-10 bg-slate-800 border border-slate-700 rounded-full flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-700 shadow-lg transition-colors"
            title="Recenter Graph"
          >
            <Target className="w-5 h-5" />
          </button>
        </div>

        {/* Enhanced Donor Sheet */}
        <Sheet open={!!selectedNode} onOpenChange={() => setSelectedNode(null)}>
          <SheetContent side="right" className="w-[380px] bg-[#0F172A]/95 backdrop-blur-xl border-l-slate-800 text-slate-200 p-0 flex flex-col">
            {selectedNode && (
              <>
                <div className="p-6 pb-0 flex-1 overflow-y-auto">
                  <div className="flex justify-between items-start mb-8">
                    <div className="flex gap-4 items-center">
                      <div className="w-14 h-14 rounded-full bg-slate-800 border-2 border-slate-700 overflow-hidden flex-shrink-0">
                        <img src={`https://api.dicebear.com/7.x/notionists/svg?seed=${selectedNode.name}`} alt="Avatar" className="w-full h-full object-cover" />
                      </div>
                      <div>
                        <h3 className="text-2xl font-serif font-bold text-white leading-tight">{selectedNode.name}</h3>
                        <div className="flex gap-2 items-center mt-1">
                          <span className="font-mono text-xs text-slate-400">{selectedNode.id}</span>
                          <span className="font-mono text-xs font-bold bg-slate-800 text-white px-1.5 py-0.5 rounded">{selectedNode.blood_type || "B+"}</span>
                        </div>
                      </div>
                    </div>
                    <div className={`px-2.5 py-1 rounded text-[10px] font-bold tracking-widest uppercase ${selectedNode.status === 'CONFIRMED' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : selectedNode.status === 'ALERTED' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' : 'bg-slate-800 text-slate-400'}`}>
                      {selectedNode.status}
                    </div>
                  </div>

                  <div className="space-y-8">
                    {/* Antigen Gauge (CSS trick) */}
                    <div>
                      <div className="text-[10px] text-slate-500 uppercase tracking-widest font-bold mb-4">Compatibility</div>
                      <div className="flex justify-center relative h-20 overflow-hidden">
                        <div className="w-40 h-40 rounded-full border-[12px] border-slate-800 absolute top-0" />
                        <div 
                          className="w-40 h-40 rounded-full border-[12px] border-teal-500 absolute top-0 transition-transform duration-1000 ease-out" 
                          style={{ clipPath: 'polygon(0 0, 100% 0, 100% 50%, 0 50%)', transform: `rotate(${((selectedNode.antigen_score || 0) * 180) - 180}deg)` }} 
                        />
                        <div className="absolute bottom-2 flex flex-col items-center">
                          <span className="text-2xl font-mono font-bold text-white">{Math.round((selectedNode.antigen_score || 0) * 100)}%</span>
                          <span className="text-[10px] text-slate-400">Match Score</span>
                        </div>
                      </div>
                    </div>

                    {/* Churn Risk */}
                    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
                      <div className="flex justify-between items-end mb-2">
                        <div className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Churn Risk (XGBoost)</div>
                        <span className="font-mono text-sm font-bold">{Math.round((selectedNode.churn_score || 0) * 100)}%</span>
                      </div>
                      <div className="flex items-center gap-3 mb-2">
                        <div className="flex-1 bg-slate-800 h-2 rounded-full overflow-hidden">
                          <div className={`h-full ${selectedNode.churn_score! > 0.7 ? 'bg-red-500' : selectedNode.churn_score! > 0.4 ? 'bg-amber-500' : 'bg-emerald-500'}`} style={{ width: `${(selectedNode.churn_score || 0) * 100}%` }} />
                        </div>
                      </div>
                      {selectedNode.churn_score! > 0.7 && (
                        <p className="text-[10px] text-red-400 flex items-center gap-1.5"><ShieldAlert className="w-3 h-3" /> High risk of donor churn detected</p>
                      )}
                    </div>

                    {/* Mini Timeline */}
                    <div>
                      <div className="text-[10px] text-slate-500 uppercase tracking-widest font-bold mb-3 flex items-center gap-2"><History className="w-3 h-3" /> Recent History</div>
                      <div className="space-y-4 pl-2 border-l-2 border-slate-800 ml-2">
                        <div className="relative">
                          <div className="absolute -left-[13px] top-1 w-2 h-2 rounded-full bg-emerald-500 ring-4 ring-[#0F172A]" />
                          <p className="text-xs text-slate-300 font-medium leading-tight">Donated 1 unit (B+)</p>
                          <p className="text-[10px] text-slate-500 mt-0.5">68 days ago</p>
                        </div>
                        <div className="relative">
                          <div className="absolute -left-[13px] top-1 w-2 h-2 rounded-full bg-teal-500 ring-4 ring-[#0F172A]" />
                          <p className="text-xs text-slate-300 font-medium leading-tight">Earned Life Saver badge</p>
                          <p className="text-[10px] text-slate-500 mt-0.5">4 months ago</p>
                        </div>
                        <div className="relative">
                          <div className="absolute -left-[13px] top-1 w-2 h-2 rounded-full bg-slate-600 ring-4 ring-[#0F172A]" />
                          <p className="text-xs text-slate-300 font-medium leading-tight">Joined inquilab AI</p>
                          <p className="text-[10px] text-slate-500 mt-0.5">2021</p>
                        </div>
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
  )
}