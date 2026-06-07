/**
 * useAgentActivity — Real-time hook for tracking LangGraph agent pipeline execution
 * and demand forecast pipeline progress via WebSocket events.
 */
import { useState, useEffect, useCallback, useRef } from 'react';

// ── Types ───────────────────────────────────────────────────────────────────

export interface AgentNodeEvent {
  node_name: string;
  node_label: string;
  request_id: string;
  status: 'running' | 'completed' | 'error';
  duration_ms?: number;
  error?: string;
  timestamp: string;
}

export interface PipelineActivity {
  request_id: string;
  patient_id: string;
  blood_type: string;
  hospital: string;
  total_nodes: number;
  started_at: string;
  completed_at?: string;
  total_ms?: number;
  outcome?: string;
  nodes: AgentNodeEvent[];
  activeNode: string | null;
}

export interface ForecastNodeEvent {
  node_name: string;
  node_label: string;
  status: 'running' | 'completed' | 'error';
  duration_ms?: number;
  detail?: string;
  shortage_count?: number;
  shortage_alerts?: string[];
  confidence_scores?: Record<string, number>;
  summary_preview?: string;
  timestamp: string;
}

export interface ForecastActivity {
  total_nodes: number;
  horizon_days: number;
  started_at: string;
  completed_at?: string;
  total_ms?: number;
  shortage_count?: number;
  blood_types?: string[];
  nodes: ForecastNodeEvent[];
  activeNode: string | null;
  isActive: boolean;
}

// Agent pipeline node order for layout
export const AGENT_PIPELINE_NODES = [
  'intake', 'eligibility', 'antigen_score', 'urgency_score',
  'neo4j_match', 'conflict', 'planner', 'outreach',
  'monitor', 'repair', 'inventory', 'voice',
  'gamification', 'outcome_node',
];

export const FORECAST_PIPELINE_NODES = [
  'data_collector', 'schedule_analyzer', 'supply_gap',
  'bedrock_insight', 'persist',
];

// ── Hook ────────────────────────────────────────────────────────────────────

const WS_URL = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL.replace(/^http/, 'ws') + '/ws/emergencies'
  : `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/emergencies`;

export function useAgentActivity() {
  const [pipelines, setPipelines] = useState<Record<string, PipelineActivity>>({});
  const [forecast, setForecast] = useState<ForecastActivity | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const dismissTimerRef = useRef<ReturnType<typeof setTimeout>>();

  // Auto-dismiss completed pipelines after delay
  const scheduleDismiss = useCallback((requestId: string) => {
    setTimeout(() => {
      setPipelines(prev => {
        const updated = { ...prev };
        delete updated[requestId];
        return updated;
      });
    }, 8000);
  }, []);

  const scheduleForecastDismiss = useCallback(() => {
    if (dismissTimerRef.current) clearTimeout(dismissTimerRef.current);
    dismissTimerRef.current = setTimeout(() => {
      setForecast(null);
    }, 10000);
  }, []);

  useEffect(() => {
    let reconnectTimer: ReturnType<typeof setTimeout>;
    let mounted = true;

    const connect = () => {
      if (!mounted) return;
      try {
        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;

        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data as string);
            const now = new Date().toISOString();

            // ── Agent Pipeline Events ──────────────────────────────────
            if (msg.type === 'pipeline_started') {
              const data = msg.data || msg;
              setPipelines(prev => ({
                ...prev,
                [data.request_id]: {
                  request_id: data.request_id,
                  patient_id: data.patient_id || '',
                  blood_type: data.blood_type || '',
                  hospital: data.hospital || '',
                  total_nodes: data.total_nodes || 14,
                  started_at: now,
                  nodes: [],
                  activeNode: null,
                }
              }));
            }

            if (msg.type === 'agent_node_started') {
              const data = msg.data || msg;
              setPipelines(prev => {
                const pipeline = prev[data.request_id];
                if (!pipeline) return prev;
                return {
                  ...prev,
                  [data.request_id]: {
                    ...pipeline,
                    activeNode: data.node_name,
                    nodes: [
                      ...pipeline.nodes,
                      {
                        node_name: data.node_name,
                        node_label: data.node_label || data.node_name,
                        request_id: data.request_id,
                        status: 'running',
                        timestamp: now,
                      }
                    ]
                  }
                };
              });
            }

            if (msg.type === 'agent_node_completed') {
              const data = msg.data || msg;
              setPipelines(prev => {
                const pipeline = prev[data.request_id];
                if (!pipeline) return prev;
                const updatedNodes = pipeline.nodes.map(n =>
                  n.node_name === data.node_name && n.status === 'running'
                    ? { ...n, status: data.status as 'completed' | 'error', duration_ms: data.duration_ms, error: data.error, timestamp: now }
                    : n
                );
                return {
                  ...prev,
                  [data.request_id]: {
                    ...pipeline,
                    activeNode: pipeline.activeNode === data.node_name ? null : pipeline.activeNode,
                    nodes: updatedNodes,
                  }
                };
              });
            }

            if (msg.type === 'pipeline_completed') {
              const data = msg.data || msg;
              setPipelines(prev => {
                const pipeline = prev[data.request_id];
                if (!pipeline) return prev;
                return {
                  ...prev,
                  [data.request_id]: {
                    ...pipeline,
                    completed_at: now,
                    total_ms: data.total_ms,
                    outcome: data.outcome,
                    activeNode: null,
                  }
                };
              });
              scheduleDismiss(data.request_id);
            }

            // ── Forecast Pipeline Events ──────────────────────────────
            if (msg.type === 'forecast_pipeline_started') {
              const data = msg.data || msg;
              if (dismissTimerRef.current) clearTimeout(dismissTimerRef.current);
              setForecast({
                total_nodes: data.total_nodes || 5,
                horizon_days: data.horizon_days || 28,
                started_at: now,
                nodes: [],
                activeNode: null,
                isActive: true,
              });
            }

            if (msg.type === 'forecast_node_started') {
              const data = msg.data || msg;
              setForecast(prev => {
                if (!prev) return prev;
                return {
                  ...prev,
                  activeNode: data.node_name,
                  nodes: [
                    ...prev.nodes,
                    {
                      node_name: data.node_name,
                      node_label: data.node_label || data.node_name,
                      status: 'running',
                      detail: data.detail,
                      timestamp: now,
                    }
                  ]
                };
              });
            }

            if (msg.type === 'forecast_node_completed') {
              const data = msg.data || msg;
              setForecast(prev => {
                if (!prev) return prev;
                const updatedNodes = prev.nodes.map(n =>
                  n.node_name === data.node_name && n.status === 'running'
                    ? {
                        ...n,
                        status: data.status as 'completed' | 'error',
                        duration_ms: data.duration_ms,
                        detail: data.detail || n.detail,
                        shortage_count: data.shortage_count,
                        shortage_alerts: data.shortage_alerts,
                        confidence_scores: data.confidence_scores,
                        summary_preview: data.summary_preview,
                        timestamp: now,
                      }
                    : n
                );
                return {
                  ...prev,
                  activeNode: prev.activeNode === data.node_name ? null : prev.activeNode,
                  nodes: updatedNodes,
                };
              });
            }

            if (msg.type === 'forecast_pipeline_completed') {
              const data = msg.data || msg;
              setForecast(prev => {
                if (!prev) return prev;
                return {
                  ...prev,
                  completed_at: now,
                  total_ms: data.total_ms,
                  shortage_count: data.shortage_count,
                  blood_types: data.blood_types,
                  activeNode: null,
                  isActive: false,
                };
              });
              scheduleForecastDismiss();
            }
          } catch {
            // non-JSON or parse error — ignore
          }
        };

        ws.onclose = () => {
          wsRef.current = null;
          if (mounted) reconnectTimer = setTimeout(connect, 5000);
        };
        ws.onerror = () => ws.close();
      } catch {
        if (mounted) reconnectTimer = setTimeout(connect, 10000);
      }
    };

    connect();
    return () => {
      mounted = false;
      clearTimeout(reconnectTimer);
      if (dismissTimerRef.current) clearTimeout(dismissTimerRef.current);
      wsRef.current?.close();
    };
  }, [scheduleDismiss, scheduleForecastDismiss]);

  // Computed: is any pipeline actively running?
  const hasActivePipeline = Object.values(pipelines).some(p => !p.completed_at);
  const activePipelines = Object.values(pipelines).filter(p => !p.completed_at || Date.now() - new Date(p.completed_at).getTime() < 8000);

  return {
    pipelines: activePipelines,
    hasActivePipeline,
    forecast,
    dismissForecast: () => setForecast(null),
  };
}
