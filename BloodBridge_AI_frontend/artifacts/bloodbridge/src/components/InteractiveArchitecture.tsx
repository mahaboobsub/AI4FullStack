import { useCallback } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  Position,
  Node,
  Edge,
  Handle
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

const CircleNode = ({ data }: any) => {
  return (
    <div className="relative flex items-center justify-center">
      <div 
        className="rounded-full shadow-md flex items-center justify-center z-10 relative transition-transform hover:scale-105 cursor-pointer" 
        style={{ backgroundColor: data.color, width: data.size || 50, height: data.size || 50 }}
      >
        {/* Invisible handles for edge connections */}
        <Handle type="target" position={Position.Left} id="l" className="opacity-0" />
        <Handle type="source" position={Position.Right} id="r" className="opacity-0" />
        <Handle type="target" position={Position.Top} id="t" className="opacity-0" />
        <Handle type="source" position={Position.Bottom} id="b" className="opacity-0" />
      </div>
      
      {data.externalLabel && (
        <div 
          className="absolute flex flex-col pointer-events-none" 
          style={data.labelStyle}
        >
          <span className="whitespace-nowrap text-[13px] text-slate-800 dark:text-slate-200 font-bold tracking-wide leading-tight">
            {data.externalLabel}
          </span>
          {data.subtext && (
            <span className="whitespace-nowrap text-[10px] text-slate-500 dark:text-slate-400 font-medium leading-tight">
              {data.subtext}
            </span>
          )}
        </div>
      )}
    </div>
  );
};

const CustomEdgeLabel = ({ label, color }: { label: string, color: string }) => (
  <div className="px-2 py-0.5 rounded border shadow-sm bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-[9px] font-mono font-bold" style={{ color }}>
    {label}
  </div>
);

const nodeTypes = {
  circle: CircleNode,
};

// Colors
const C_ACTOR = '#f88214'; // Orange
const C_FRONT = '#06b6d4'; // Cyan
const C_API = '#475569';   // Slate
const C_ML = '#10B981';    // Green
const C_DB = '#e11d48';    // Rose
const C_LLM = '#6366f1';   // Indigo

const initialNodes: Node[] = [
  // --- ACTORS ---
  { id: 'patient', type: 'circle', data: { color: C_ACTOR, externalLabel: 'Patient', subtext: 'Requester', labelStyle: { right: '120%', textAlign: 'right' } }, position: { x: 50, y: 100 } },
  { id: 'ngo', type: 'circle', data: { color: C_ACTOR, externalLabel: 'NGO Staff', subtext: 'Coordinator', labelStyle: { right: '120%', textAlign: 'right' } }, position: { x: 50, y: 220 } },
  { id: 'donor', type: 'circle', data: { color: C_ACTOR, externalLabel: 'Donor', subtext: 'Responder', labelStyle: { right: '120%', textAlign: 'right' } }, position: { x: 50, y: 340 } },

  // --- FRONTEND ---
  { id: 'web', type: 'circle', data: { color: C_FRONT, size: 60, externalLabel: 'Web Dashboards', subtext: 'React + Vite', labelStyle: { top: '-40px', left: '50%', transform: 'translateX(-50%)', textAlign: 'center' } }, position: { x: 250, y: 150 } },
  { id: 'telegram', type: 'circle', data: { color: C_FRONT, size: 60, externalLabel: 'Telegram Bot', subtext: 'Agentic UI', labelStyle: { top: '-40px', left: '50%', transform: 'translateX(-50%)', textAlign: 'center' } }, position: { x: 250, y: 300 } },

  // --- API ---
  { id: 'api', type: 'circle', data: { color: C_API, size: 70, externalLabel: 'FastAPI Gateway', subtext: 'Routing & Auth', labelStyle: { top: '-40px', left: '50%', transform: 'translateX(-50%)', textAlign: 'center' } }, position: { x: 450, y: 220 } },

  // --- BACKEND (LANGGRAPH / ML) ---
  { id: 'pillarA', type: 'circle', data: { color: C_ML, size: 60, externalLabel: 'Pillar A', subtext: 'Smart Matching (XGBoost)', labelStyle: { left: '120%' } }, position: { x: 650, y: 80 } },
  { id: 'pillarB', type: 'circle', data: { color: C_ML, size: 60, externalLabel: 'Pillar B', subtext: 'Autonomous Coordination', labelStyle: { left: '120%' } }, position: { x: 650, y: 220 } },
  { id: 'pillarC', type: 'circle', data: { color: C_ML, size: 60, externalLabel: 'Pillar C', subtext: 'Engagement (Churn ML)', labelStyle: { left: '120%' } }, position: { x: 650, y: 360 } },
  { id: 'bedrock', type: 'circle', data: { color: C_LLM, size: 60, externalLabel: 'Amazon Bedrock', subtext: 'Nova / Sonnet 3.5', labelStyle: { top: '120%', left: '50%', transform: 'translateX(-50%)', textAlign: 'center' } }, position: { x: 800, y: 480 } },

  // --- DATA LAYER ---
  { id: 'neo4j', type: 'circle', data: { color: C_DB, size: 60, externalLabel: 'Neo4j Aura', subtext: 'Graph DB', labelStyle: { left: '120%' } }, position: { x: 950, y: 100 } },
  { id: 'supabase', type: 'circle', data: { color: C_DB, size: 60, externalLabel: 'Supabase', subtext: 'PostgreSQL', labelStyle: { left: '120%' } }, position: { x: 950, y: 220 } },
  { id: 'eraktkosh', type: 'circle', data: { color: C_DB, size: 60, externalLabel: 'e-RaktKosh', subtext: 'External API', labelStyle: { left: '120%' } }, position: { x: 950, y: 340 } },
];

const initialEdges: Edge[] = [
  // Actors -> Frontend
  { id: 'e1', source: 'patient', target: 'web', sourceHandle: 'r', targetHandle: 'l', animated: true, style: { stroke: '#94a3b8' } },
  { id: 'e2', source: 'ngo', target: 'web', sourceHandle: 'r', targetHandle: 'l', animated: true, style: { stroke: '#94a3b8' } },
  { id: 'e3', source: 'donor', target: 'telegram', sourceHandle: 'r', targetHandle: 'l', animated: true, style: { stroke: '#94a3b8' } },

  // Frontend -> API
  { id: 'e4', source: 'web', target: 'api', sourceHandle: 'r', targetHandle: 'l', animated: true, style: { stroke: '#94a3b8' } },
  { id: 'e5', source: 'telegram', target: 'api', sourceHandle: 'r', targetHandle: 'l', animated: true, style: { stroke: '#94a3b8' } },

  // API -> Pillars
  { id: 'e6', source: 'api', target: 'pillarA', sourceHandle: 'r', targetHandle: 'l', style: { stroke: C_ML, strokeWidth: 1.5 } },
  { id: 'e7', source: 'api', target: 'pillarB', sourceHandle: 'r', targetHandle: 'l', style: { stroke: C_ML, strokeWidth: 1.5 } },
  { id: 'e8', source: 'api', target: 'pillarC', sourceHandle: 'r', targetHandle: 'l', style: { stroke: C_ML, strokeWidth: 1.5 } },

  // Pillars -> LLM
  { id: 'e9', source: 'pillarA', target: 'bedrock', sourceHandle: 'b', targetHandle: 't', style: { stroke: C_LLM, strokeDasharray: '4 4' }, label: <CustomEdgeLabel label="Tool Calling" color={C_LLM} /> },
  { id: 'e10', source: 'pillarB', target: 'bedrock', sourceHandle: 'b', targetHandle: 't', style: { stroke: C_LLM, strokeDasharray: '4 4' } },
  { id: 'e11', source: 'pillarC', target: 'bedrock', sourceHandle: 'b', targetHandle: 't', style: { stroke: C_LLM, strokeDasharray: '4 4' } },

  // Pillars -> Data
  { id: 'e12', source: 'pillarA', target: 'neo4j', sourceHandle: 'r', targetHandle: 'l', animated: true, style: { stroke: C_DB } },
  { id: 'e13', source: 'pillarA', target: 'supabase', sourceHandle: 'r', targetHandle: 'l', style: { stroke: C_DB } },
  
  { id: 'e14', source: 'pillarB', target: 'neo4j', sourceHandle: 'r', targetHandle: 'l', animated: true, style: { stroke: C_DB } },
  { id: 'e15', source: 'pillarB', target: 'supabase', sourceHandle: 'r', targetHandle: 'l', animated: true, style: { stroke: C_DB } },
  { id: 'e16', source: 'pillarB', target: 'eraktkosh', sourceHandle: 'r', targetHandle: 'l', style: { stroke: C_DB } },

  { id: 'e17', source: 'pillarC', target: 'supabase', sourceHandle: 'r', targetHandle: 'l', style: { stroke: C_DB } },
];

export default function InteractiveArchitecture() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  return (
    <div className="w-full h-[600px] border border-[#E8E0D8] dark:border-slate-800 rounded-xl bg-slate-50/50 dark:bg-[#0A0F1C]/50 overflow-hidden shadow-sm relative transition-colors duration-500">
      {/* Title Overlay */}
      <div className="absolute top-4 left-6 z-10 pointer-events-none">
        <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 tracking-wider uppercase">System Architecture Flow</h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-sm">
          End-to-end data flow from Clients to AI Services and Data Layer.
        </p>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        minZoom={0.3}
        maxZoom={1.5}
        attributionPosition="bottom-right"
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#94a3b8" gap={20} size={1} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
