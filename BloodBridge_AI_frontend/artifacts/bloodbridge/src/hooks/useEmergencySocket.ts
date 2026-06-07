import { useState, useEffect, useRef } from 'react';
import { toast } from 'sonner';
import { getActiveEmergencies } from '@/lib/api';
import type { Emergency } from '@/lib/api';

const WS_URL = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL.replace(/^http/, 'ws') + '/ws/emergencies'
  : `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/emergencies`;

export function useEmergencySocket() {
  const [emergencies, setEmergencies] = useState<Emergency[]>([]);
  const [confirmedToday, setConfirmedToday] = useState(0);
  const [chainBreak, setChainBreak] = useState<{ patient_id: string; position: number } | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Initial fetch via REST (fast hydration before WS connects)
  useEffect(() => {
    getActiveEmergencies()
      .then(setEmergencies)
      .catch(() => setEmergencies([]));
  }, []);

  // Real WebSocket for live chain updates
  useEffect(() => {
    let reconnectTimer: ReturnType<typeof setTimeout>;
    let mounted = true;

    const connect = () => {
      if (!mounted) return;
      try {
        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log('[inquilab AI] WebSocket connected');
        };

        ws.onmessage = (event) => {
          try {
            const rawMsg = JSON.parse(event.data as string);
            const msg = {
              ...rawMsg,
              ...(rawMsg.data && typeof rawMsg.data === 'object' ? rawMsg.data : {})
            };

            if (msg.type === 'chain_update' || msg.type === 'chain_repaired') {
              // Full refresh of emergencies list
              getActiveEmergencies().then(setEmergencies).catch(() => {});
              if (msg.new_donor_name) {
                toast.success(`${msg.new_donor_name} confirmed for position ${msg.position}`);
              }
            }

            if (msg.type === 'chain_break') {
              setChainBreak({ patient_id: msg.patient_id, position: msg.position });
              toast.error(
                `Chain break — ${msg.patient_id} · Position ${msg.position} · Auto-repair running`,
                { duration: 10000 }
              );
              setTimeout(() => setChainBreak(null), 8000);
            }

            if (msg.type === 'emergency_created' || msg.type === 'pipeline_started') {
              getActiveEmergencies().then(setEmergencies).catch(() => {});
              toast.info(`New emergency: ${msg.blood_type || '?'} needed at ${msg.hospital || 'Hospital'}`);
            }

            if (msg.type === 'donor_confirmed') {
              setConfirmedToday((n) => n + 1);
              setEmergencies(prev => {
                const updated = structuredClone(prev);
                let matched = false;
                for (const em of updated) {
                  const node = em.chain.find(
                    (n) =>
                      (msg.donor_id && n.donor_id === msg.donor_id) ||
                      (msg.donor_name && n.donor_name === msg.donor_name)
                  );
                  if (node) {
                    node.status = 'CONFIRMED';
                    node.confirmed_at = new Date().toISOString();
                    toast.success(`${node.donor_name} confirmed for ${em.patient_id}`);
                    matched = true;
                    break;
                  }
                }
                if (!matched) {
                  getActiveEmergencies().then(setEmergencies).catch(() => {});
                }
                return updated;
              });
            }

            if (msg.type === 'donor_declined') {
              setEmergencies(prev => {
                const updated = structuredClone(prev);
                for (const em of updated) {
                  const node = em.chain.find(n => n.donor_name === msg.donor_name);
                  if (node) {
                    node.status = 'DECLINED';
                    toast.warning(`${msg.donor_name} declined (position ${msg.position})`);
                    break;
                  }
                }
                return updated;
              });
            }

            if (msg.type === 'chain_repair_started') {
              toast.info(`🔧 Chain repair started for ${msg.request_id || 'request'}`, { duration: 5000 });
            }

            if (msg.type === 'emergency_escalated') {
              toast.error(`🚨 Emergency escalated for ${msg.patient_id || 'patient'} — staff intervention required`, { duration: 15000 });
              getActiveEmergencies().then(setEmergencies).catch(() => {});
            }

            if (msg.type === 'emergency_completed') {
              getActiveEmergencies().then(setEmergencies).catch(() => {});
              toast.success(`Emergency ${msg.request_id} completed: ${msg.outcome}`, { duration: 8000 });
            }

            if (msg.type === 'voice_call_result') {
              toast.info(`Voice call result for ${msg.donor_id}: ${msg.result}`, { duration: 5000 });
            }

            if (msg.type === 'ocr_scan_complete') {
              toast.success(
                `Blood card scanned: ${msg.donor_id} — ${msg.blood_group || '?'} (${msg.antigen_summary || 'antigens'})`,
                { duration: 8000 }
              );
            }

            if (msg.type === 'chain_monitor_update') {
              if (msg.action === 'voice_escalation') {
                toast.warning(`No reply in 1 min — calling ${msg.donor_name || msg.donor_id}`, { duration: 8000 });
              }
            }

            if (msg.type === 'voice_call_active') {
              toast.info(`Bolna call started for ${msg.donor_id}`, { duration: 5000 });
            }

            // ── Agent Pipeline Live Events ──────────────────────────────
            if (msg.type === 'pipeline_started') {
              const d = msg.data || msg;
              toast('🚀 AI Pipeline Activated', {
                description: `${d.blood_type || '?'} for patient ${d.patient_id || '?'} — 14 agents dispatched`,
                duration: 6000,
              });
            }

            if (msg.type === 'pipeline_completed') {
              const d = msg.data || msg;
              toast.success('✅ AI Pipeline Complete', {
                description: `${d.request_id || 'Request'} finished in ${((d.total_ms || 0) / 1000).toFixed(1)}s — outcome: ${d.outcome || 'N/A'}`,
                duration: 8000,
              });
            }

            // ── Forecast Pipeline Events ────────────────────────────────
            if (msg.type === 'forecast_pipeline_started') {
              toast('📊 Demand Forecast Running', {
                description: 'Analyzing blood supply and demand across all blood types...',
                duration: 4000,
              });
            }

            if (msg.type === 'forecast_node_completed') {
              const d = msg.data || msg;
              if (d.node_name === 'supply_gap' && d.shortage_count > 0) {
                toast.warning(`⚠️ ${d.shortage_count} Shortage Alert${d.shortage_count > 1 ? 's' : ''} Detected`, {
                  description: 'XGBoost analysis found supply-demand gaps',
                  duration: 6000,
                });
              }
            }

            if (msg.type === 'forecast_pipeline_completed') {
              const d = msg.data || msg;
              toast.success('📊 Forecast Complete', {
                description: `28-day forecast generated in ${((d.total_ms || 0) / 1000).toFixed(1)}s`,
                duration: 6000,
              });
            }
          } catch {
            // non-JSON ping/pong or binary — ignore
          }
        };

        ws.onerror = () => {
          ws.close();
        };

        ws.onclose = () => {
          wsRef.current = null;
          // Reconnect after 5 seconds if still mounted
          if (mounted) {
            reconnectTimer = setTimeout(connect, 5000);
          }
        };
      } catch {
        // WebSocket not available (no backend) — gracefully do nothing
        if (mounted) {
          reconnectTimer = setTimeout(connect, 10000);
        }
      }
    };

    connect();

    return () => {
      mounted = false;
      clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, []);

  const activeConfirmed = emergencies.reduce(
    (sum, em) => sum + em.chain.filter((c) => c.status === 'CONFIRMED' || c.status === 'COMPLETED').length,
    0
  );

  return {
    emergencies,
    setEmergencies,
    chainBreak,
    confirmedToday: Math.max(confirmedToday, activeConfirmed),
  };
}
