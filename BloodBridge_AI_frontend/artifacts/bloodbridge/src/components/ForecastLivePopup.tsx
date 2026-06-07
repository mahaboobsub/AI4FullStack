/**
 * ForecastLivePopup — Premium real-time modal showing demand forecast pipeline
 * progress step-by-step with special XGBoost highlight, animated timeline,
 * and live shortage alert popups.
 */
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, Loader2, XCircle, X, TrendingUp, AlertTriangle, Brain, Database, Calendar, BarChart3, Save } from 'lucide-react';
import { useAgentActivity, FORECAST_PIPELINE_NODES, type ForecastActivity } from '@/hooks/useAgentActivity';

// ── Node config ─────────────────────────────────────────────────────────────

const FORECAST_NODE_CONFIG: Record<string, { icon: typeof TrendingUp; color: string; label: string; description: string }> = {
  data_collector: {
    icon: Database,
    color: 'blue',
    label: 'Data Collection',
    description: 'Scanning bridges and emergency records from Supabase',
  },
  schedule_analyzer: {
    icon: Calendar,
    color: 'violet',
    label: 'Schedule Analysis',
    description: 'Analyzing 4-week transfusion calendar for all blood types',
  },
  supply_gap: {
    icon: BarChart3,
    color: 'amber',
    label: 'XGBoost Supply Gap',
    description: 'Running ML model to compute demand vs supply analysis',
  },
  bedrock_insight: {
    icon: Brain,
    color: 'teal',
    label: 'Bedrock AI Summary',
    description: 'Generating AI-powered insights with Bedrock Claude',
  },
  persist: {
    icon: Save,
    color: 'emerald',
    label: 'Persist & Alert',
    description: 'Saving forecast to database and dispatching alerts',
  },
};

const COLOR_MAP: Record<string, { bg: string; text: string; border: string; glow: string }> = {
  blue:    { bg: 'bg-blue-500/15',    text: 'text-blue-400',    border: 'border-blue-500/30',    glow: 'shadow-[0_0_20px_rgba(59,130,246,0.2)]' },
  violet:  { bg: 'bg-violet-500/15',  text: 'text-violet-400',  border: 'border-violet-500/30',  glow: 'shadow-[0_0_20px_rgba(139,92,246,0.2)]' },
  amber:   { bg: 'bg-amber-500/15',   text: 'text-amber-400',   border: 'border-amber-500/30',   glow: 'shadow-[0_0_20px_rgba(245,158,11,0.2)]' },
  teal:    { bg: 'bg-teal-500/15',    text: 'text-teal-400',    border: 'border-teal-500/30',    glow: 'shadow-[0_0_20px_rgba(20,184,166,0.2)]' },
  emerald: { bg: 'bg-emerald-500/15', text: 'text-emerald-400', border: 'border-emerald-500/30', glow: 'shadow-[0_0_20px_rgba(16,185,129,0.2)]' },
};

// ── Forecast Node Step ──────────────────────────────────────────────────────

function ForecastStep({ nodeName, forecast, index }: { nodeName: string; forecast: ForecastActivity; index: number }) {
  const config = FORECAST_NODE_CONFIG[nodeName];
  const colors = COLOR_MAP[config.color];
  const nodeEvent = forecast.nodes.find(n => n.node_name === nodeName);
  const isActive = forecast.activeNode === nodeName;
  const isCompleted = nodeEvent?.status === 'completed';
  const isError = nodeEvent?.status === 'error';
  const isPending = !nodeEvent;
  const IconComponent = config.icon;
  const isXGBoost = nodeName === 'supply_gap';

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05, type: 'spring', stiffness: 300, damping: 25 }}
      className={`relative flex gap-4 ${isPending ? 'opacity-40' : 'opacity-100'} transition-opacity duration-500`}
    >
      {/* Timeline connector */}
      <div className="flex flex-col items-center flex-shrink-0">
        <motion.div
          className={`relative w-10 h-10 rounded-xl flex items-center justify-center border transition-all duration-500 ${
            isActive
              ? `${colors.bg} ${colors.border} ${colors.glow}`
              : isCompleted
              ? 'bg-emerald-500/15 border-emerald-500/30'
              : isError
              ? 'bg-red-500/15 border-red-500/30'
              : 'bg-white/[0.03] border-white/[0.06]'
          }`}
          animate={isActive ? { scale: [1, 1.08, 1] } : {}}
          transition={isActive ? { repeat: Infinity, duration: 2, ease: 'easeInOut' } : {}}
        >
          {isActive && (
            <motion.div
              className={`absolute inset-0 rounded-xl ${colors.bg} ${colors.border} border`}
              animate={{ opacity: [0.5, 0, 0.5] }}
              transition={{ repeat: Infinity, duration: 2 }}
            />
          )}
          {isActive ? (
            <Loader2 className={`w-5 h-5 ${colors.text} animate-spin relative z-10`} />
          ) : isCompleted ? (
            <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', stiffness: 500, damping: 15 }}>
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            </motion.div>
          ) : isError ? (
            <XCircle className="w-5 h-5 text-red-400" />
          ) : (
            <IconComponent className="w-5 h-5 text-white/20" />
          )}
        </motion.div>
        {index < FORECAST_PIPELINE_NODES.length - 1 && (
          <div className={`w-0.5 flex-1 min-h-[16px] transition-colors duration-500 ${
            isCompleted ? 'bg-emerald-500/40' : 'bg-white/[0.06]'
          }`} />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 pb-5">
        <div className="flex items-center gap-2 mb-0.5">
          <span className={`text-sm font-semibold transition-colors duration-300 ${
            isActive ? colors.text : isCompleted ? 'text-white/90' : 'text-white/30'
          }`}>
            {config.label}
          </span>
          {isXGBoost && isActive && (
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded bg-amber-500/20 text-amber-400 border border-amber-500/30 animate-pulse">
              ML MODEL
            </span>
          )}
          {nodeEvent?.duration_ms !== undefined && (
            <span className="text-[10px] text-white/30 font-mono">{nodeEvent.duration_ms}ms</span>
          )}
        </div>

        <p className={`text-[11px] leading-relaxed transition-colors duration-300 ${
          isActive ? 'text-white/60' : isCompleted ? 'text-white/40' : 'text-white/20'
        }`}>
          {nodeEvent?.detail || config.description}
        </p>

        {/* XGBoost special: show shortage alerts as they come in */}
        {isXGBoost && isCompleted && nodeEvent?.shortage_alerts && nodeEvent.shortage_alerts.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mt-2 space-y-1"
          >
            {nodeEvent.shortage_alerts.map((alert, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.15 }}
                className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-red-500/10 border border-red-500/20 text-[10px] text-red-300"
              >
                <AlertTriangle className="w-3 h-3 flex-shrink-0 text-red-400" />
                <span className="truncate">{alert}</span>
              </motion.div>
            ))}
          </motion.div>
        )}

        {/* Confidence scores */}
        {isXGBoost && isCompleted && nodeEvent?.confidence_scores && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="mt-2 flex flex-wrap gap-1.5"
          >
            {Object.entries(nodeEvent.confidence_scores).map(([bt, score]) => (
              <div
                key={bt}
                className={`px-2 py-0.5 rounded text-[9px] font-mono border ${
                  (score as number) >= 0.8 ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
                  (score as number) >= 0.5 ? 'bg-amber-500/10 border-amber-500/20 text-amber-400' :
                  'bg-red-500/10 border-red-500/20 text-red-400'
                }`}
              >
                {bt}: {Math.round((score as number) * 100)}%
              </div>
            ))}
          </motion.div>
        )}

        {/* Bedrock AI summary preview */}
        {nodeName === 'bedrock_insight' && isCompleted && nodeEvent?.summary_preview && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-2 px-3 py-2 rounded-lg bg-teal-500/8 border border-teal-500/15 text-[10px] text-teal-300/80 italic leading-relaxed"
          >
            "{nodeEvent.summary_preview}..."
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}

// ── Main Popup Component ────────────────────────────────────────────────────

export default function ForecastLivePopup() {
  const { forecast, dismissForecast } = useAgentActivity();

  if (!forecast) return null;

  const completedNodes = forecast.nodes.filter(n => n.status === 'completed').length;
  const isCompleted = !forecast.isActive && forecast.completed_at;
  const progress = Math.round((completedNodes / forecast.total_nodes) * 100);

  return (
    <AnimatePresence>
      <motion.div
        key="forecast-overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[70] flex items-center justify-center p-4"
      >
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          onClick={isCompleted ? dismissForecast : undefined}
        />

        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, y: 30, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 30, scale: 0.95 }}
          transition={{ type: 'spring', stiffness: 300, damping: 25 }}
          className="forecast-popup-card relative w-full max-w-lg max-h-[85vh] overflow-y-auto"
        >
          {/* Header */}
          <div className="sticky top-0 z-10 px-6 pt-5 pb-4 border-b border-white/[0.06] bg-[rgba(10,15,30,0.95)] backdrop-blur-xl">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${isCompleted ? 'bg-emerald-500/15 border border-emerald-500/30' : 'bg-teal-500/15 border border-teal-500/30'}`}>
                  {isCompleted ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  ) : (
                    <TrendingUp className="w-5 h-5 text-teal-400" />
                  )}
                </div>
                <div>
                  <h2 className="text-base font-bold text-white flex items-center gap-2">
                    Demand Forecast Pipeline
                    {!isCompleted && (
                      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded bg-red-500/20 text-red-400 border border-red-500/20">
                        <div className="w-1 h-1 rounded-full bg-red-400 animate-pulse" />
                        RUNNING
                      </span>
                    )}
                  </h2>
                  <p className="text-[11px] text-white/40 font-mono mt-0.5">
                    {forecast.horizon_days}-day forecast · {completedNodes}/{forecast.total_nodes} nodes
                    {forecast.total_ms && ` · ${(forecast.total_ms / 1000).toFixed(1)}s`}
                  </p>
                </div>
              </div>
              {isCompleted && (
                <button onClick={dismissForecast} className="p-1.5 rounded-lg hover:bg-white/10 text-white/40 transition-colors">
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Progress bar */}
            <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
              <motion.div
                className={`h-full rounded-full ${isCompleted ? 'bg-gradient-to-r from-emerald-500 to-emerald-400' : 'bg-gradient-to-r from-teal-600 via-teal-500 to-teal-400'}`}
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.6, ease: 'easeOut' }}
              />
            </div>
          </div>

          {/* Pipeline Steps */}
          <div className="px-6 pt-5 pb-4">
            {FORECAST_PIPELINE_NODES.map((nodeName, index) => (
              <ForecastStep key={nodeName} nodeName={nodeName} forecast={forecast} index={index} />
            ))}
          </div>

          {/* Completion banner */}
          <AnimatePresence>
            {isCompleted && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mx-6 mb-5 px-4 py-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center gap-3"
              >
                <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                <div>
                  <div className="text-sm font-semibold text-emerald-400">Forecast Complete</div>
                  <div className="text-[10px] text-emerald-400/60 mt-0.5">
                    {forecast.shortage_count
                      ? `${forecast.shortage_count} shortage alerts for ${forecast.blood_types?.join(', ') || 'blood types'}`
                      : 'No shortage alerts — supply looks healthy'
                    }
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
