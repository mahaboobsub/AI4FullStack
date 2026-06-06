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
  is_active?: boolean;
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

// ── V2: New Response Types ──────────────────────────────────────────────────
export interface DonorRank {
  donor_id: string; city: string; rank: number; lives_saved: number;
}
export interface ActiveRequest {
  request_id: string; patient_first_name: string; patient_age: number | null;
  blood_type: string; hospital: string; city: string;
  urgency_score: number | null; urgency_level: string;
  compatibility_score: number | null; chain_position: number; alerted_at: string | null;
}
export interface ScheduleEntry {
  schedule_id: number; patient_id: string; scheduled_date: string;
  hospital: string; blood_type: string; status: string;
  request_id: string | null; days_until: number | null;
}
export interface ChainHistoryEntry {
  request_id: string; blood_type: string; hospital: string;
  city: string; status: string; created_at: string; completed_at: string | null;
  confirmed_donors: number; total_chain_size: number;
  donors: { name: string; position: number; status: string; antigen_score: number | null; confirmed_at: string | null }[];
}

// ── Config ──────────────────────────────────────────────────────────────────
const BASE = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL.replace(/\/$/, "")
  : "";

const STAFF_TOKEN = import.meta.env.VITE_STAFF_TOKEN || "";

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem("auth_token");
  return token ? { "Authorization": `Bearer ${token}` } : {};
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

export async function getActiveEmergencies(): Promise<Emergency[]> {
  return apiFetch<Emergency[]>("/api/emergencies");
}

export async function getChainStatus(id: string): Promise<ChainNode[]> {
  return apiFetch<ChainNode[]>(`/api/emergencies/${id}/chain`);
}

export async function getGraphData(requestId?: string): Promise<{ nodes: GraphNode[]; links: GraphLink[] }> {
  const qs = requestId ? `?request_id=${encodeURIComponent(requestId)}` : "";
  return apiFetch<{ nodes: GraphNode[]; links: GraphLink[] }>(`/api/donors/graph/data${qs}`);
}

export async function getBloodStock(city: string, bloodType?: string): Promise<BloodBank[]> {
  const qs = new URLSearchParams({ city });
  if (bloodType) qs.set("bloodType", bloodType);
  return apiFetch<BloodBank[]>(`/api/blood-banks?${qs}`);
}

export async function getDonors(): Promise<Donor[]> {
  return apiFetch<Donor[]>("/api/donors");
}

export async function getDonor(id: string): Promise<Donor> {
  return apiFetch<Donor>(`/api/donors/${id}`);
}

export async function getDonorImpactStories(id: string): Promise<string[]> {
  try {
    const mem = await apiFetch<{ impact_stories?: string[] }>(`/api/donors/${id}/memory`);
    return mem.impact_stories || [];
  } catch {
    return [];
  }
}

export async function getLeaderboard(city: string): Promise<LeaderboardEntry[]> {
  return apiFetch<LeaderboardEntry[]>(`/api/donors/leaderboard?city=${encodeURIComponent(city)}`);
}

export async function getSystemHealth(): Promise<ServiceHealth[]> {
  return apiFetch<ServiceHealth[]>("/api/health");
}

export async function getAgentTraces(): Promise<AgentTrace[]> {
  return apiFetch<AgentTrace[]>("/api/admin/traces", { headers: getAuthHeaders() });
}

export async function getAnalytics(): Promise<EngagementMetrics> {
  return apiFetch<EngagementMetrics>("/api/admin/analytics", { headers: getAuthHeaders() });
}

export async function getPatientProfile(id: string): Promise<PatientProfile> {
  return apiFetch<PatientProfile>(`/api/patients/${id}`);
}

export async function triggerEmergency(data: EmergencyRequest): Promise<{ requestId: string }> {
  return apiFetch<{ requestId: string }>("/api/emergencies", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function triggerVoiceCall(id: string): Promise<{ callSid: string }> {
  return apiFetch<{ callSid: string }>(`/api/donors/${id}/trigger-voice`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
}

export async function triggerOutreach(id: string): Promise<{ messageId: string }> {
  return apiFetch<{ messageId: string }>(`/api/donors/${id}/trigger-outreach`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
}

export async function confirmOutcome(id: string): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>(`/api/emergencies/${id}/confirm`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
}

export async function retrainModels(): Promise<{ jobId: string }> {
  return apiFetch<{ jobId: string }>("/api/admin/retrain", {
    method: "POST",
    headers: getAuthHeaders(),
  });
}

export async function updateAgentConfig(config: Record<string, unknown>): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>("/api/admin/config", {
    method: "POST",
    body: JSON.stringify(config),
    headers: getAuthHeaders(),
  });
}

export async function addStaffMember(data: { username: string; hospital: string; role: string }): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>("/api/admin/staff", {
    method: "POST",
    body: JSON.stringify(data),
    headers: getAuthHeaders(),
  });
}

// ── Auth Endpoints ──────────────────────────────────────────────────────────

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

// ── V2: New API Endpoints ─────────────────────────────────────────────────────

export async function getDonorByLookup(params: { phone?: string; telegram_chat_id?: string }): Promise<Donor> {
  const qs = new URLSearchParams();
  if (params.phone) qs.set("phone", params.phone);
  if (params.telegram_chat_id) qs.set("telegram_chat_id", params.telegram_chat_id);
  return apiFetch<Donor>(`/api/donors/lookup?${qs}`);
}

export async function getDonorRank(id: string): Promise<DonorRank> {
  return apiFetch<DonorRank>(`/api/donors/${id}/rank`);
}

export async function getDonorActiveRequest(id: string): Promise<ActiveRequest | null> {
  return apiFetch<ActiveRequest | null>(`/api/donors/${id}/active-request`);
}

export async function setDonorAvailability(id: string, available: boolean, until?: string): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>(`/api/donors/${id}/availability`, {
    method: "POST",
    body: JSON.stringify({ available, until }),
  });
}

export async function getPatientSchedule(id: string, status?: string): Promise<ScheduleEntry[]> {
  const qs = status ? `?status_filter=${encodeURIComponent(status)}` : "";
  return apiFetch<ScheduleEntry[]>(`/api/patients/${id}/schedule${qs}`);
}

export async function getPatientChainHistory(id: string, limit?: number): Promise<ChainHistoryEntry[]> {
  const qs = limit ? `?limit=${limit}` : "";
  return apiFetch<ChainHistoryEntry[]>(`/api/patients/${id}/chain-history${qs}`);
}

// ── M4: Multi-Location Types + APIs ───────────────────────────────────────────
export interface LocationEntry {
  location_id: string; label: string; lat: number; lng: number;
  geohash: string; is_primary: boolean; priority_order: number;
}
export interface NewLocation {
  label: string; lat: number; lng: number; is_primary?: boolean; priority_order?: number;
}

// Patient locations (max 5)
export async function getPatientLocations(id: string): Promise<LocationEntry[]> {
  return apiFetch<LocationEntry[]>(`/api/patients/${id}/locations`);
}
export async function addPatientLocation(id: string, loc: NewLocation): Promise<{ success: boolean; location: LocationEntry }> {
  return apiFetch(`/api/patients/${id}/locations`, { method: "POST", body: JSON.stringify(loc) });
}
export async function deletePatientLocation(id: string, locationId: string): Promise<{ success: boolean }> {
  return apiFetch(`/api/patients/${id}/locations/${locationId}`, { method: "DELETE" });
}
export async function setPatientPrimaryLocation(id: string, locationId: string): Promise<{ success: boolean }> {
  return apiFetch(`/api/patients/${id}/locations/${locationId}`, { method: "PATCH", body: JSON.stringify({ is_primary: true }) });
}

// Donor backup locations (soft-limit 10)
export async function getDonorLocations(id: string): Promise<LocationEntry[]> {
  return apiFetch<LocationEntry[]>(`/api/donors/${id}/locations`);
}
export async function addDonorLocation(id: string, loc: NewLocation): Promise<{ success: boolean; location: LocationEntry }> {
  return apiFetch(`/api/donors/${id}/locations`, { method: "POST", body: JSON.stringify(loc) });
}
export async function deleteDonorLocation(id: string, locationId: string): Promise<{ success: boolean }> {
  return apiFetch(`/api/donors/${id}/locations/${locationId}`, { method: "DELETE" });
}
export async function setDonorPrimaryLocation(id: string, locationId: string): Promise<{ success: boolean }> {
  return apiFetch(`/api/donors/${id}/locations/${locationId}`, { method: "PATCH", body: JSON.stringify({ is_primary: true }) });
}

// ── M5: Donor Health Self-Update ──────────────────────────────────────────────
export interface HealthStatusBody {
  available: boolean; reason?: string; hold_until?: string; note?: string;
}
export async function updateDonorHealthStatus(id: string, body: HealthStatusBody): Promise<{ success: boolean; donor_id: string; available: boolean }> {
  return apiFetch(`/api/donors/${id}/health-status`, { method: "POST", body: JSON.stringify(body) });
}

// ── A5: Demand Forecast ───────────────────────────────────────────────────────
export interface DemandForecast {
  generated_at: string;
  forecast_horizon_days: number;
  forecast_json: { week_label: string; blood_type_counts: Record<string, number> }[];
  supply_json: Record<string, number>;
  shortage_alerts: string[];
  ai_summary: string;
  blood_type_breakdown: Record<string, number>;
  message?: string;
}
export async function getDemandForecast(): Promise<DemandForecast> {
  return apiFetch<DemandForecast>("/api/admin/forecast", { headers: getAuthHeaders() });
}
export async function runDemandForecast(): Promise<{ status: string; message: string }> {
  return apiFetch("/api/admin/forecast/run", { method: "POST", headers: getAuthHeaders() });
}
