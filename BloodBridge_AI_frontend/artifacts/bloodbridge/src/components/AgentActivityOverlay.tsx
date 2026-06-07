/**
 * AgentActivityOverlay — A premium glassmorphism floating panel that displays
 * real-time LangGraph agent node execution as the pipeline runs.
 * Appears automatically when an emergency pipeline starts, showing each node
 * transitioning through running → completed states with beautiful animations.
 */
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, Loader2, XCircle, Zap, ChevronDown, ChevronUp, X } from 'lucide-react';
import { useState } from 'react';
import { useAgentActivity, AGENT_PIPELINE_NODES, type PipelineActivity } from '@/hooks/useAgentActivity';

// ── Node icon mapping ───────────────────────────────────────────────────────

const NODE_ICONS: Record<string, string> = {
  intake: '📋', eligibility: '✅', antigen_score: '🧬', urgency_score: '⚡',
  neo4j_match: '🔗', conflict: '⚔️', planner: '📐', outreach: '📡',
  monitor: '👁️', repair: '🔧', inventory: '📦', voice: '📞',
  gamification: '🏆', outcome_node: '🎯',
};

function getNodeStatus(pipeline: PipelineActivity, nodeName: string) {
  const nodeEvent = pipeline.nodes.find(n => n.node_name === nodeName);
  if (!nodeEvent) return 'pending';
  return nodeEvent.status;
}

function getNodeDuration(pipeline: PipelineActivity, nodeName: string) {
  const nodeEvent = pipeline.nodes.find(n => n.node_name === nodeName);
  return nodeEvent?.duration_ms;
}

function getNodeLabel(nodeName: string): string {
  const labels: Record<string, string> = {
    intake: 'Patient Intake', eligibility: 'Eligibility Check',
    antigen_score: 'Antigen Scoring', urgency_score: 'Urgency Scoring',
    neo4j_match: 'Neo4j Match', conflict: 'Conflict Resolver',
    planner: 'Outreach Planner', outreach: 'Donor Outreach',
    monitor: 'Chain Monitor', repair: 'Chain Repair',
    inventory: 'Inventory Fallback', voice: 'Voice Call',
    gamification: 'Gamification', outcome_node: 'Outcome',
  };
  return labels[nodeName] || nodeName;
}

// ── Single Pipeline Card ────────────────────────────────────────────────────

function PipelineCard({ pipeline }: { pipeline: PipelineActivity }) {
  const [expanded, setExpanded] = useState(true);
  const completedNodes = pipeline.nodes.filter(n => n.status === 'completed').length;
  const isCompleted = !!pipeline.completed_at;
  const progress = Math.round((completedNodes / 14) * 100);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 20, scale: 0.9 }}
      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
      className="agent-overlay-card"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <div className={`relative w-8 h-8 rounded-lg flex items-center justify-center ${isCompleted ? 'bg-emerald-500/20' : 'bg-teal-500/20'}`}>
            {isCompleted ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            ) : (
              <>
                <Zap className="w-4 h-4 text-teal-400" />
                <div className="absolute inset-0 rounded-lg bg-teal-400/20 animate-ping" />
              </>
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-white/90">AI Pipeline</span>
              {!isCompleted && (
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded bg-red-500/20 text-red-400 border border-red-500/20">
                  <div className="w-1 h-1 rounded-full bg-red-400 animate-pulse" />
                  LIVE
                </span>
              )}
              {isCompleted && (
                <span className="px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/20">
                  DONE
                </span>
              )}
            </div>
            <div className="text-[10px] text-white/40 font-mono mt-0.5">
              {pipeline.request_id} · {pipeline.blood_type} · {pipeline.hospital || 'Hospital'}
            </div>
          </div>
        </div>
        <button onClick={() => setExpanded(!expanded)} className="p-1 rounded hover:bg-white/10 text-white/40 transition-colors">
          {expanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Progress bar */}
      <div className="px-4 py-2">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[10px] text-white/50 font-mono">{completedNodes}/14 nodes</span>
          {pipeline.total_ms && (
            <span className="text-[10px] text-white/50 font-mono">{(pipeline.total_ms / 1000).toFixed(1)}s total</span>
          )}
        </div>
        <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
          <motion.div
            className={`h-full rounded-full ${isCompleted ? 'bg-gradient-to-r from-emerald-500 to-emerald-400' : 'bg-gradient-to-r from-teal-600 to-teal-400'}`}
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          />
        </div>
      </div>

      {/* Node grid */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-3 grid grid-cols-2 gap-1">
              {AGENT_PIPELINE_NODES.map((nodeName) => {
                const status = getNodeStatus(pipeline, nodeName);
                const duration = getNodeDuration(pipeline, nodeName);
                const icon = NODE_ICONS[nodeName] || '⚙️';
                const isActive = pipeline.activeNode === nodeName;

                return (
                  <motion.div
                    key={nodeName}
                    layout
                    className={`flex items-center gap-2 px-2 py-1.5 rounded-md text-[10px] transition-all duration-300 ${
                      isActive
                        ? 'bg-teal-500/15 border border-teal-500/30 shadow-[0_0_12px_rgba(20,184,166,0.15)]'
                        : status === 'completed'
                        ? 'bg-emerald-500/8 border border-emerald-500/15'
                        : status === 'error'
                        ? 'bg-red-500/10 border border-red-500/20'
                        : 'bg-white/[0.02] border border-white/[0.04]'
                    }`}
                  >
                    <span className="text-xs flex-shrink-0">{icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className={`font-medium truncate ${
                        isActive ? 'text-teal-300' :
                        status === 'completed' ? 'text-emerald-400/90' :
                        status === 'error' ? 'text-red-400' :
                        'text-white/30'
                      }`}>
                        {getNodeLabel(nodeName)}
                      </div>
                    </div>
                    <div className="flex-shrink-0">
                      {isActive && <Loader2 className="w-3 h-3 text-teal-400 animate-spin" />}
                      {status === 'completed' && !isActive && (
                        <div className="flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                          {duration !== undefined && (
                            <span className="text-[9px] text-white/30 font-mono">{duration}ms</span>
                          )}
                        </div>
                      )}
                      {status === 'error' && <XCircle className="w-3 h-3 text-red-400" />}
                    </div>
                  </motion.div>
                );
              })}
            </div>

            {/* Active node message */}
            {pipeline.activeNode && (
              <div className="px-4 pb-3">
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-teal-500/[0.08] border border-teal-500/20">
                  <div className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse flex-shrink-0" />
                  <span className="text-[10px] text-teal-300 font-mono">
                    Running {getNodeLabel(pipeline.activeNode)}...
                  </span>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ── Main Overlay Component ──────────────────────────────────────────────────

export default function AgentActivityOverlay() {
  const { pipelines } = useAgentActivity();

  if (pipelines.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[60] flex flex-col gap-3 max-h-[80vh] overflow-y-auto pointer-events-auto" style={{ width: '380px' }}>
      <AnimatePresence mode="popLayout">
        {pipelines.map((pipeline) => (
          <PipelineCard key={pipeline.request_id} pipeline={pipeline} />
        ))}
      </AnimatePresence>
    </div>
  );
}
