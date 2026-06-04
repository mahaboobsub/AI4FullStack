import { useState, useEffect, lazy, Suspense, useRef, useCallback } from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { getGraphData, type GraphNode, type GraphLink } from "@/lib/api";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Phone, MessageSquare, ShieldAlert, Target, Info, Search, History } from "lucide-react";
import { toast } from "sonner";
import type { ForceGraphMethods } from "react-force-graph-2d";

const ForceGraph2D = lazy(() => import("react-force-graph-2d"));

export default function Graph() {
  const [data, setData] = useState<{nodes: GraphNode[], links: GraphLink[]}>({ nodes: [], links: [] });
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const graphRef = useRef<ForceGraphMethods>();

  useEffect(() => {
    document.documentElement.classList.add("dark");
    getGraphData().then(setData);
  }, []);

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
          {/* Glassmorphism Command Bar */}
          <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-xl px-4 py-2 shadow-2xl flex items-center gap-4 w-[500px]">
            <Search className="w-4 h-4 text-slate-400" />
            <div className="h-4 w-px bg-slate-700" />
            <select className="bg-transparent border-0 text-slate-200 text-sm outline-none focus:ring-0 flex-1 appearance-none cursor-pointer">
              <option className="bg-slate-900">Patient P-10234 (B+)</option>
              <option className="bg-slate-900">Patient P-10891 (A-)</option>
            </select>
            <div className="h-4 w-px bg-slate-700" />
            <select className="bg-transparent border-0 text-slate-200 text-sm outline-none focus:ring-0 appearance-none cursor-pointer pr-4">
              <option className="bg-slate-900">All Statuses</option>
              <option className="bg-slate-900">Confirmed</option>
              <option className="bg-slate-900">Alerted</option>
            </select>
            <div className="flex gap-1 ml-auto">
              <kbd className="bg-slate-800 border border-slate-700 rounded px-1.5 py-0.5 text-[10px] font-mono text-slate-400">⌘</kbd>
              <kbd className="bg-slate-800 border border-slate-700 rounded px-1.5 py-0.5 text-[10px] font-mono text-slate-400">F</kbd>
            </div>
          </div>

          <Suspense fallback={<div className="w-full h-full flex items-center justify-center text-teal-500">Loading Intelligence Layer...</div>}>
            <ForceGraph2D
              ref={graphRef}
              graphData={data}
              backgroundColor="#0A0F1C"
              nodeRelSize={6}
              linkColor={(link: any) => {
                if (link.status === "CONFIRMED") return "rgba(16,185,129,0.6)";
                if (link.status === "ALERTED") return "rgba(245,158,11,0.4)";
                if (link.status === "DECLINED") return "rgba(239,68,68,0.3)";
                return "rgba(51,65,85,0.4)";
              }}
              linkWidth={(link: any) => link.antigen_score ? link.antigen_score * 3 : 1}
              nodeCanvasObject={(node: any, ctx, globalScale) => {
                const label = node.name;
                const fontSize = 10/globalScale;
                
                if (node.type === "patient") {
                  // Patient Node: Large red circle with P
                  ctx.fillStyle = "#EF4444";
                  ctx.beginPath();
                  ctx.arc(node.x, node.y, 10, 0, 2 * Math.PI, false);
                  ctx.fill();
                  
                  ctx.fillStyle = "#ffffff";
                  ctx.font = `bold ${12/globalScale}px monospace`;
                  ctx.textAlign = 'center';
                  ctx.textBaseline = 'middle';
                  ctx.fillText("P", node.x, node.y);
                  
                  // Glow ring
                  ctx.strokeStyle = "rgba(239,68,68,0.3)";
                  ctx.lineWidth = 2/globalScale;
                  ctx.beginPath();
                  ctx.arc(node.x, node.y, 14, 0, 2 * Math.PI, false);
                  ctx.stroke();

                } else if (node.type === "hospital") {
                  // Hospital Node: Square with H
                  ctx.fillStyle = "#475569";
                  ctx.fillRect(node.x - 8, node.y - 8, 16, 16);
                  ctx.strokeStyle = "#94A3B8";
                  ctx.lineWidth = 1/globalScale;
                  ctx.strokeRect(node.x - 8, node.y - 8, 16, 16);
                  
                  ctx.fillStyle = "#ffffff";
                  ctx.font = `bold ${10/globalScale}px monospace`;
                  ctx.textAlign = 'center';
                  ctx.textBaseline = 'middle';
                  ctx.fillText("H", node.x, node.y);
                } else {
                  // Donor Node
                  const isConfirmed = node.status === "CONFIRMED";
                  ctx.fillStyle = isConfirmed ? "#10B981" : node.status === "ALERTED" ? "#FBBF24" : node.status === "DECLINED" ? "#EF4444" : "#475569";
                  ctx.beginPath();
                  ctx.arc(node.x, node.y, 6, 0, 2 * Math.PI, false);
                  ctx.fill();
                  
                  if (isConfirmed) {
                    ctx.shadowColor = '#10B981';
                    ctx.shadowBlur = 10;
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, 6, 0, 2 * Math.PI, false);
                    ctx.fill();
                    ctx.shadowBlur = 0;
                  }

                  // Initial letter
                  ctx.fillStyle = "#ffffff";
                  ctx.font = `bold ${8/globalScale}px sans-serif`;
                  ctx.textAlign = 'center';
                  ctx.textBaseline = 'middle';
                  ctx.fillText(node.name.charAt(0), node.x, node.y);
                  
                  // Churn risk ring
                  if (node.churn_score && node.churn_score > 0.5) {
                    ctx.strokeStyle = node.churn_score > 0.7 ? "rgba(239,68,68,0.8)" : "rgba(245,158,11,0.8)";
                    ctx.lineWidth = 1.5/globalScale;
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, 9, 0, 2 * Math.PI, false);
                    ctx.stroke();
                  }
                }
                
                // Label below node
                ctx.font = `${fontSize}px Sans-Serif`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'top';
                ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
                ctx.fillText(label, node.x, node.y + 12);
              }}
              onNodeClick={handleNodeClick}
              onEngineStop={centerGraph}
            />
          </Suspense>

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
                          <p className="text-xs text-slate-300 font-medium leading-tight">Joined BloodBridge</p>
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