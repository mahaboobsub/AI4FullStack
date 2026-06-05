/**
 * BloodBridge AI — API Client
 * ============================
 * All functions make real HTTP calls to the FastAPI backend.
 * In development, Vite proxies /api → http://localhost:8000 automatically.
 *
 * Admin endpoints require X-Staff-Token header (set VITE_STAFF_TOKEN in .env).
 * On error, functions return mock/fallback data so the UI never breaks.
 */

// ── Types matching backend Pydantic schemas ─────────────────────────────────
export type Priority      = "CRITICAL" | "HIGH" | "ROUTINE";
export type ChainStatus   = "CONFIRMED" | "ALERTED" | "DECLINED" | "PENDING" | "VOICE" | "COMPLETED";
export type ChurnRisk     = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
export type ServiceStatus = "online" | "degraded" | "offline";
export type Outcome       = "SUCCESS" | "ESCALATED" | "IN_PROGRESS";
export type NodeStatus    = "success" | "fallback" | "error";

export interface ChainNode {
  donor_id: string; donor_name: string; chain_position: number;
  status: ChainStatus; antigen_score: number;
  alerted_at?: string; confirmed_at?: string;
}
export interface Emergency {
  request_id: string; patient_id: string; blood_type: string; city: string;
  priority: Priority; urgency_score: number; hospital_name: string; ward?: string;
  status: string; chain: ChainNode[]; created_at: string;
}
export interface GraphNode {
  id: string; type: "donor" | "patient" | "hospital";
  name: string; status?: ChainStatus; antigen_score?: number; churn_score?: number;
  blood_type?: string; donation_count?: number; badges?: string[];
}
export interface GraphLink { source: string; target: string; antigen_score: number; status: string; }
export interface BloodBank {
  id: string; name: string; city: string; lat: number; lng: number; contact: string;
  units: Record<string, number>; distance_km: number; drive_min: number;
}
export interface Donor {
  donor_id: string; name: string; blood_type: string; city: string;
  kell_negative: boolean; churn_score: number; churn_risk: ChurnRisk;
  donation_count: number; lives_saved: number; last_donation_days: number;
  response_rate: number; badges: string[]; preferred_language: string;
  antigen_score?: number; telegram_chat_id?: string;
}
export interface LeaderboardEntry {
  rank: number; name: string; city: string; lives_saved: number;
  donation_count: number; badges: string[];
}
export interface ServiceHealth {
  service: string; host: string; status: ServiceStatus; latency_ms: number; uptime_pct: number;
}
export interface TraceNode { name: string; status: NodeStatus; duration_ms: number; }
export interface AgentTrace {
  request_id: string; patient_id: string; timestamp: string;
  outcome: Outcome; node_count: number; total_ms: number; nodes: TraceNode[];
}
export interface EngagementMetrics {
  active_donors: number; total_donors: number; active_pct: number;
  at_risk_count: number; avg_response_rate: number; donated_this_month: number;
  trend: { date: string; active_pct: number }[];
  by_city: { city: string; donations: number }[];
}
export interface EmergencyRequest {
  patient_id: string; blood_type: string; city: string; ward: string; hospital: string;
}
export interface PatientProfile {
  patient_id: string; name: string; age: number; blood_type: string;
  hospital: string; ward: string; transfusion_count: number;
  next_transfusion_due: string; hemoglobin: number; status: "CRITICAL" | "STABLE" | "OVERDUE";
  antibody_flags: string[]; kell_negative: boolean;
  linked_donors: { donor_id: string; donor_name: string; antigen_score: number; status: ChainStatus; donation_count: number; badges: string[] }[];
  transfusion_history: { date: string; donor_name: string; blood_type: string; outcome: string }[];
  active_request?: string;
}

// ── Config ──────────────────────────────────────────────────────────────────
// Vite proxy handles /api → backend in dev. For production, set VITE_API_URL.
const BASE = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL.replace(/\/$/, "")
  : "";

// Staff token for admin endpoints — set VITE_STAFF_TOKEN in .env
const STAFF_TOKEN = import.meta.env.VITE_STAFF_TOKEN || "";

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem("auth_token");
  return token ? { "Authorization": "Bearer $token" } : {};
}

async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const url = `${BASE}${path}`;
  const resp = await fetch(url, {
    headers: { "Content-Type": "application/json", ...init.headers },
    ...init,
  });
  if (!resp.ok) {
    const err = await resp.text();
    throw new Error(`API ${resp.status}: ${err}`);
  }
  return resp.json() as Promise<T>;
}

// ── MOCK STAFF (kept for Admin page display) ─────────────────────────────────
export const MOCK_STAFF = [
  { username: "@dr_priya_kims",  hospital: "KIMS Secunderabad",   role: "Coordinator", added: "May 12, 2025" },
  { username: "@rahul_apollo",   hospital: "Apollo Banjara Hills", role: "Staff",       added: "May 18, 2025" },
  { username: "@admin_bb",       hospital: "Blood Warriors HQ",   role: "Admin",       added: "Apr 2, 2025"  },
];

// ── API Functions ─────────────────────────────────────────────────────────────

/**
 * GET /api/emergencies — Active emergency requests with donor chains
 */
export async function getActiveEmergencies(): Promise<Emergency[]> {
  return apiFetch<Emergency[]>("/api/emergencies");
}

/**
 * GET /api/emergencies/{id}/chain — Chain status for a specific emergency
 */
export async function getChainStatus(id: string): Promise<ChainNode[]> {
  return apiFetch<ChainNode[]>(`/api/emergencies/${id}/chain`);
}

/**
 * GET /api/donors/graph/data — Graph nodes and links for the Graph dashboard
 */
export async function getGraphData(requestId?: string): Promise<{ nodes: GraphNode[]; links: GraphLink[] }> {
  const qs = requestId ? `?request_id=${encodeURIComponent(requestId)}` : "";
  return apiFetch<{ nodes: GraphNode[]; links: GraphLink[] }>(`/api/donors/graph/data${qs}`);
}

/**
 * GET /api/blood-banks?city=&bloodType= — Blood bank inventory by city
 */
export async function getBloodStock(city: string, bloodType?: string): Promise<BloodBank[]> {
  const qs = new URLSearchParams({ city });
  if (bloodType) qs.set("bloodType", bloodType);
  return apiFetch<BloodBank[]>(`/api/blood-banks?${qs}`);
}

/**
 * GET /api/donors — All donors sorted by churn score descending
 */
export async function getDonors(): Promise<Donor[]> {
  return apiFetch<Donor[]>("/api/donors");
}

/**
 * GET /api/donors/leaderboard?city= — City leaderboard
 */
export async function getLeaderboard(city: string): Promise<LeaderboardEntry[]> {
  return apiFetch<LeaderboardEntry[]>(`/api/donors/leaderboard?city=${encodeURIComponent(city)}`);
}

/**
 * GET /api/health — System service health (from admin router)
 */
export async function getSystemHealth(): Promise<ServiceHealth[]> {
  return apiFetch<ServiceHealth[]>("/api/health");
}

/**
 * GET /api/admin/traces — Last 5 agent execution traces (admin only)
 */
export async function getAgentTraces(): Promise<AgentTrace[]> {
  return apiFetch<AgentTrace[]>("/api/admin/traces", { headers: getAuthHeaders() });
}

/**
 * GET /api/admin/analytics — Donor engagement metrics (admin only)
 */
export async function getAnalytics(): Promise<EngagementMetrics> {
  return apiFetch<EngagementMetrics>("/api/admin/analytics", { headers: getAuthHeaders() });
}

/**
 * GET /api/patients/{id} — Full patient profile with chain and history
 */
export async function getPatientProfile(id: string): Promise<PatientProfile> {
  return apiFetch<PatientProfile>(`/api/patients/${id}`);
}

/**
 * POST /api/emergencies — Create a new emergency and trigger the pipeline
 */
export async function triggerEmergency(data: EmergencyRequest): Promise<{ requestId: string }> {
  return apiFetch<{ requestId: string }>("/api/emergencies", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * POST /api/donors/{id}/trigger-voice — Manually trigger Bolna voice call (admin only)
 */
export async function triggerVoiceCall(id: string): Promise<{ callSid: string }> {
  return apiFetch<{ callSid: string }>(`/api/donors/${id}/trigger-voice`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
}

/**
 * POST /api/donors/{id}/trigger-outreach — Manually trigger Telegram message (admin only)
 */
export async function triggerOutreach(id: string): Promise<{ messageId: string }> {
  return apiFetch<{ messageId: string }>(`/api/donors/${id}/trigger-outreach`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
}

/**
 * POST /api/emergencies/{id}/confirm — Mark emergency as resolved
 */
export async function confirmOutcome(id: string): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>(`/api/emergencies/${id}/confirm`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
}

/**
 * POST /api/admin/retrain — Trigger ML model retraining job (admin only)
 */
export async function retrainModels(): Promise<{ jobId: string }> {
  return apiFetch<{ jobId: string }>("/api/admin/retrain", {
    method: "POST",
    headers: getAuthHeaders(),
  });
}

/**
 * POST /api/admin/config — Update agent orchestration config (admin only)
 */
export async function updateAgentConfig(config: Record<string, unknown>): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>("/api/admin/config", {
    method: "POST",
    body: JSON.stringify(config),
    headers: getAuthHeaders(),
  });
}

/**
 * POST /api/admin/staff — Add a new staff coordinator (admin only)
 */
export async function addStaffMember(data: { username: string; hospital: string; role: string }): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>("/api/admin/staff", {
    method: "POST",
    body: JSON.stringify(data),
    headers: getAuthHeaders(),
  });
}

// -- Auth Endpoints ----------------------------------------------------------

export async function login(identifier: string, password: string, role: string): Promise<{ access_token: string; user: any }> {
  return apiFetch<{ access_token: string; user: any }>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ identifier, password, role }),
  });
}

export async function signup(data: any): Promise<{ success: boolean; user: any }> {
  return apiFetch<{ success: boolean; user: any }>("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

