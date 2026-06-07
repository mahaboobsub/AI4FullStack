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

const CustomEdgeLabel = ({ label, color }: { label: string; color: string }) => (
  <div
    className="px-2 py-0.5 rounded border shadow-sm bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-[9px] font-mono font-bold"
    style={{ color }}
  >
    {label}
  </div>
);

const nodeTypes = {
  circle: CircleNode,
};

// Layer colors
const C_FRONT = '#06b6d4';   // Cyan — Frontend
const C_API = '#475569';     // Slate — REST API hub
const C_BACKEND = '#10B981'; // Green — Backend processing
const C_DB = '#e11d48';      // Rose — Data stores
const C_LLM = '#6366f1';     // Indigo — AWS Bedrock
const C_COMMS = '#f88214';   // Orange — Telegram / Voice

const initialNodes: Node[] = [
  // ── Frontend (React + Vite) ──────────────────────────────────────────────
  {
    id: 'staffDashboard',
    type: 'circle',
    data: {
      color: C_FRONT,
      size: 58,
      externalLabel: 'Staff Dashboard',
      subtext: 'Emergency · Graph · Map · Admin',
      labelStyle: { right: '115%', textAlign: 'right' },
    },
    position: { x: 40, y: 40 },
  },
  {
    id: 'patientPortal',
    type: 'circle',
    data: {
      color: C_FRONT,
      size: 52,
      externalLabel: 'Patient Portal',
      subtext: 'Schedules · Locations',
      labelStyle: { right: '115%', textAlign: 'right' },
    },
    position: { x: 40, y: 150 },
  },
  {
    id: 'donorPortal',
    type: 'circle',
    data: {
      color: C_FRONT,
      size: 52,
      externalLabel: 'Donor Portal',
      subtext: 'Engagement · Bridges',
      labelStyle: { right: '115%', textAlign: 'right' },
    },
    position: { x: 40, y: 260 },
  },
  {
    id: 'wsHook',
    type: 'circle',
    data: {
      color: C_FRONT,
      size: 48,
      externalLabel: 'WebSocket Hook',
      subtext: 'useAgentActivity',
      labelStyle: { right: '115%', textAlign: 'right' },
    },
    position: { x: 40, y: 380 },
  },

  // ── Backend (FastAPI) ────────────────────────────────────────────────────
  {
    id: 'restApi',
    type: 'circle',
    data: {
      color: C_API,
      size: 72,
      externalLabel: 'REST API',
      subtext: 'FastAPI Gateway',
      labelStyle: { top: '-44px', left: '50%', transform: 'translateX(-50%)', textAlign: 'center' },
    },
    position: { x: 340, y: 200 },
  },
  {
    id: 'langGraph',
    type: 'circle',
    data: {
      color: C_BACKEND,
      size: 62,
      externalLabel: 'LangGraph Pipeline',
      subtext: '14 agent nodes',
      labelStyle: { top: '-44px', left: '50%', transform: 'translateX(-50%)', textAlign: 'center' },
    },
    position: { x: 560, y: 60 },
  },
  {
    id: 'matchingEngine',
    type: 'circle',
    data: {
      color: C_BACKEND,
      size: 58,
      externalLabel: 'Matching Engine',
      subtext: 'Geo + weighted scoring',
      labelStyle: { top: '-44px', left: '50%', transform: 'translateX(-50%)', textAlign: 'center' },
    },
    position: { x: 560, y: 200 },
  },
  {
    id: 'cron',
    type: 'circle',
    data: {
      color: C_BACKEND,
      size: 52,
      externalLabel: 'APScheduler',
      subtext: 'Monitor · Churn · Forecast',
      labelStyle: { top: '-44px', left: '50%', transform: 'translateX(-50%)', textAlign: 'center' },
    },
    position: { x: 560, y: 360 },
  },

  // ── Data & External Services ─────────────────────────────────────────────
  {
    id: 'supabase',
    type: 'circle',
    data: {
      color: C_DB,
      size: 58,
      externalLabel: 'Supabase',
      subtext: 'Donors · Patients · Chains',
      labelStyle: { left: '115%' },
    },
    position: { x: 820, y: 40 },
  },
  {
    id: 'neo4j',
    type: 'circle',
    data: {
      color: C_DB,
      size: 58,
      externalLabel: 'Neo4j',
      subtext: 'Chain state · Graph viz',
      labelStyle: { left: '115%' },
    },
    position: { x: 820, y: 150 },
  },
  {
    id: 'bedrock',
    type: 'circle',
    data: {
      color: C_LLM,
      size: 58,
      externalLabel: 'AWS Bedrock',
      subtext: 'Claude Haiku / Sonnet',
      labelStyle: { left: '115%' },
    },
    position: { x: 820, y: 260 },
  },
  {
    id: 'telegram',
    type: 'circle',
    data: {
      color: C_COMMS,
      size: 52,
      externalLabel: 'Telegram Bot',
      subtext: 'Primary outreach',
      labelStyle: { left: '115%' },
    },
    position: { x: 820, y: 370 },
  },
  {
    id: 'bolna',
    type: 'circle',
    data: {
      color: C_COMMS,
      size: 52,
      externalLabel: 'Bolna.ai Voice',
      subtext: 'Fallback calls',
      labelStyle: { left: '115%' },
    },
    position: { x: 820, y: 480 },
  },
];

const initialEdges: Edge[] = [
  // Frontend → REST API
  { id: 'e1', source: 'staffDashboard', target: 'restApi', sourceHandle: 'r', targetHandle: 'l', animated: true, style: { stroke: '#94a3b8' } },
  { id: 'e2', source: 'patientPortal', target: 'restApi', sourceHandle: 'r', targetHandle: 'l', animated: true, style: { stroke: '#94a3b8' } },
  { id: 'e3', source: 'donorPortal', target: 'restApi', sourceHandle: 'r', targetHandle: 'l', animated: true, style: { stroke: '#94a3b8' } },

  // WebSocket ↔ REST API (bidirectional live events)
  {
    id: 'e4',
    source: 'wsHook',
    target: 'restApi',
    sourceHandle: 'r',
    targetHandle: 'l',
    animated: true,
    style: { stroke: C_FRONT, strokeWidth: 1.5 },
    label: <CustomEdgeLabel label="live events" color={C_FRONT} />,
  },
  {
    id: 'e5',
    source: 'restApi',
    target: 'wsHook',
    sourceHandle: 'l',
    targetHandle: 'r',
    animated: true,
    style: { stroke: C_FRONT, strokeWidth: 1.5, strokeDasharray: '4 4' },
  },

  // REST API → Backend services
  { id: 'e6', source: 'restApi', target: 'langGraph', sourceHandle: 'r', targetHandle: 'l', style: { stroke: C_BACKEND, strokeWidth: 1.5 } },
  { id: 'e7', source: 'restApi', target: 'matchingEngine', sourceHandle: 'r', targetHandle: 'l', style: { stroke: C_BACKEND, strokeWidth: 1.5 } },

  // Cron → LangGraph
  {
    id: 'e8',
    source: 'cron',
    target: 'langGraph',
    sourceHandle: 't',
    targetHandle: 'b',
    style: { stroke: C_BACKEND, strokeDasharray: '4 4' },
    label: <CustomEdgeLabel label="scheduled" color={C_BACKEND} />,
  },

  // LangGraph → Matching Engine
  { id: 'e9', source: 'langGraph', target: 'matchingEngine', sourceHandle: 'b', targetHandle: 't', animated: true, style: { stroke: C_BACKEND } },

  // LangGraph → Data & External
  { id: 'e10', source: 'langGraph', target: 'supabase', sourceHandle: 'r', targetHandle: 'l', animated: true, style: { stroke: C_DB } },
  { id: 'e11', source: 'langGraph', target: 'neo4j', sourceHandle: 'r', targetHandle: 'l', style: { stroke: C_DB } },
  {
    id: 'e12',
    source: 'langGraph',
    target: 'bedrock',
    sourceHandle: 'r',
    targetHandle: 'l',
    style: { stroke: C_LLM, strokeDasharray: '4 4' },
    label: <CustomEdgeLabel label="LLM tiers" color={C_LLM} />,
  },
  { id: 'e13', source: 'langGraph', target: 'telegram', sourceHandle: 'r', targetHandle: 'l', animated: true, style: { stroke: C_COMMS } },
  { id: 'e14', source: 'langGraph', target: 'bolna', sourceHandle: 'r', targetHandle: 'l', style: { stroke: C_COMMS, strokeDasharray: '4 4' } },

  // Matching Engine → Supabase
  { id: 'e15', source: 'matchingEngine', target: 'supabase', sourceHandle: 'r', targetHandle: 'l', animated: true, style: { stroke: C_DB } },
];

export default function InteractiveArchitecture() {
  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  return (
    <div className="w-full h-[600px] border border-[#E8E0D8] dark:border-slate-800 rounded-xl bg-slate-50/50 dark:bg-[#0A0F1C]/50 overflow-hidden shadow-sm relative transition-colors duration-500">
      {/* Title Overlay */}
      <div className="absolute top-4 left-6 z-10 pointer-events-none">
        <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 tracking-wider uppercase">
          High-Level Architecture
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-sm">
          Frontend dashboards, FastAPI backend, LangGraph agents, and external services.
        </p>
      </div>

      {/* Layer labels */}
      <div className="absolute top-4 right-6 z-10 pointer-events-none flex flex-col gap-1.5 text-right">
        <span className="text-[9px] font-mono font-bold uppercase tracking-widest text-cyan-600 dark:text-cyan-400">Frontend</span>
        <span className="text-[9px] font-mono font-bold uppercase tracking-widest text-slate-500">Backend</span>
        <span className="text-[9px] font-mono font-bold uppercase tracking-widest text-rose-500">Data &amp; Services</span>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.12 }}
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
