import { useState, useEffect, useRef } from 'react';
import { toast } from 'sonner';
import { getActiveEmergencies } from '@/lib/api';
import type { Emergency } from '@/lib/api';

const WS_URL = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL.replace(/^http/, 'ws') + '/ws/emergencies'
  : `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/emergencies`;

export function useEmergencySocket() {
  const [emergencies, setEmergencies] = useState<Emergency[]>([]);
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
          console.log('[BloodBridge] WebSocket connected');
        };

        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data as string);

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

            if (msg.type === 'emergency_created') {
              getActiveEmergencies().then(setEmergencies).catch(() => {});
              toast.info(`New emergency: ${msg.blood_type} needed at ${msg.hospital}`);
            }

            if (msg.type === 'donor_confirmed') {
              setEmergencies(prev => {
                const updated = structuredClone(prev);
                for (const em of updated) {
                  const node = em.chain.find(n => n.donor_id === msg.donor_id);
                  if (node) {
                    node.status = 'CONFIRMED';
                    node.confirmed_at = new Date().toISOString();
                    toast.success(`${node.donor_name} confirmed for ${em.patient_id}`);
                    break;
                  }
                }
                return updated;
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

  return { emergencies, setEmergencies, chainBreak };
}
