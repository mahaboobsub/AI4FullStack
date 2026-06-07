/**
 * inquilab AI — API Client
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
  antigen_panel?: Record<string, string>; kell_negative?: boolean;
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
    // 202 Accepted is not "ok" by fetch but is success-with-deferral — surface a typed error
    const error = new Error(`API ${resp.status}: ${err}`) as Error & { status: number };
    error.status = resp.status;
    throw error;
  }
  return resp.json() as Promise<T>;
}

// Generate RFC4122 v4 UUID for idempotency keys (no external dep)
function genIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return "ik-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
}

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
    headers: { "Content-Type": "application/json", "X-Idempotency-Key": genIdempotencyKey() },
  });
}

// triggerVoiceCall returns INITIATED, but the backend returns 202 when call is
// queued outside TRAI safe hours. Surface that distinction to the UI cleanly.
export type VoiceCallResult =
  | { status: "INITIATED"; callSid: string }
  | { status: "QUEUED"; reason: string }
  | { status: "ERROR"; message: string };

export async function triggerVoiceCall(id: string): Promise<VoiceCallResult> {
  try {
    const r = await apiFetch<{ callSid: string }>(`/api/donors/${id}/voice`, {
      method: "POST",
      headers: getAuthHeaders(),
    });
    return { status: "INITIATED", callSid: r.callSid };
  } catch (err: unknown) {
    const e = err as Error & { status?: number };
    // 202 is "queued for TRAI safe hours" — backend uses HTTPException(202)
    if (e.status === 202) {
      return {
        status: "QUEUED",
        reason: e.message.replace(/^API 202:\s*/, "").replace(/^\{.*"detail":"|"\}$/g, ""),
      };
    }
    return { status: "ERROR", message: e.message };
  }
}

export async function triggerOutreach(id: string): Promise<{ messageId: string }> {
  return apiFetch<{ messageId: string }>(`/api/donors/${id}/outreach`, {
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
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
  });
}

export async function addStaffMember(data: { username: string; hospital: string; role: string }): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>("/api/admin/staff", {
    method: "POST",
    body: JSON.stringify(data),
    headers: getAuthHeaders(),
  });
}

export async function getStaffMembers(): Promise<{ username: string; hospital: string; role: string; added: string }[]> {
  return apiFetch<{ username: string; hospital: string; role: string; added: string }[]>(
    "/api/admin/staff",
    { headers: getAuthHeaders() }
  );
}

export async function deleteStaffMember(username: string): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>(`/api/admin/staff/${encodeURIComponent(username)}`, {
    method: "DELETE",
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

// ── Auto-schedule + Hungarian optimizer ─────────────────────────────────────

export async function triggerAutoSchedule(patientId: string): Promise<{ success: boolean; message: string }> {
  return apiFetch(`/api/patients/${patientId}/auto-schedule`, { method: "POST" });
}

export interface OptimizerAssignment {
  donor_id: string;
  name?: string;
  ring?: number;
  match_score?: number;
  distance_km?: number;
}

export interface OptimizeAssignmentsResult {
  assignments: Record<string, OptimizerAssignment[]>;
  patient_count?: number;
  message: string;
}

export async function optimizeAssignments(): Promise<OptimizeAssignmentsResult> {
  return apiFetch<OptimizeAssignmentsResult>("/api/admin/optimize-assignments", {
    method: "POST",
    headers: getAuthHeaders(),
  });
}

export interface AgentConfig {
  coordination_timeout_mins: number;
  channel_sequence: string[];
  retry_limit: number;
  safe_calling_hours: { start: number; end: number };
  demo_mock_mode?: boolean;
  app_env?: string;
}

export async function getAgentConfig(): Promise<AgentConfig> {
  return apiFetch<AgentConfig>("/api/admin/config", { headers: getAuthHeaders() });
}

// ── DPDP 2023 Self-Service (consent / erasure / access) ────────────────────────
export interface ConsentSummary {
  donor_id: string;
  consents: Record<string, "granted" | "revoked" | "not_given">;
  last_updated?: string;
}

export async function getConsentSummary(donorId: string): Promise<ConsentSummary> {
  return apiFetch<ConsentSummary>(`/api/donors/${donorId}/consent`);
}

export async function revokeConsent(
  donorId: string,
  consentType: "all" | "sms" | "voice" | "telegram" | "data_storage" | "data_sharing_bloodwarriors" | "data_sharing_hospitals"
): Promise<{ success: boolean; message: string }> {
  return apiFetch(`/api/donors/${donorId}/consent/revoke`, {
    method: "POST",
    body: JSON.stringify({ consent_type: consentType }),
  });
}

// DPDP §11 — Right to Access (export all donor data)
export async function exportDonorData(donorId: string): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(`/api/donors/${donorId}/my-data`);
}

// DPDP §12 — Right to Erasure (delete all donor data)
export async function eraseDonorData(donorId: string): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>(`/api/donors/${donorId}/data`, {
    method: "DELETE",
  });
}

// ── Donor eligibility (already-implemented endpoint) ───────────────────────────
export interface EligibilityResult {
  eligible: boolean;
  reason: string | null;
  days_until_eligible: number | null;
}

export async function getDonorEligibility(donorId: string): Promise<EligibilityResult> {
  return apiFetch<EligibilityResult>(`/api/donors/${donorId}/eligibility`);
}

// ── e-RaktKosh Refresh ────────────────────────────────────────────────────────
export async function refreshBloodBanks(): Promise<{ success: boolean; message: string }> {
  return apiFetch("/api/blood-banks/refresh", { method: "POST", headers: getAuthHeaders() });
}

// ── Emergency Trace (per-request LangGraph execution trace) ────────────────────
export interface EmergencyTrace {
  request_id: string;
  nodes: TraceNode[];
  total_ms: number;
  outcome: Outcome;
}

export async function getEmergencyTrace(id: string): Promise<EmergencyTrace> {
  return apiFetch<EmergencyTrace>(`/api/emergencies/${id}/trace`, { headers: getAuthHeaders() });
}

// ── Schedule Entries (admin view) ──────────────────────────────────────────────
export async function getScheduleEntries(): Promise<ScheduleEntry[]> {
  return apiFetch<ScheduleEntry[]>("/api/schedule", { headers: getAuthHeaders() });
}

// ── Card OCR Upload ────────────────────────────────────────────────────────────
export interface CardOcrResult {
  blood_group: string | null;
  name: string | null;
  antigen_panel: Record<string, "Positive" | "Negative">;
  antigen_flags: Record<string, boolean>;
}

export async function uploadBloodCard(file: File): Promise<CardOcrResult> {
  const formData = new FormData();
  formData.append("file", file);
  const url = `${BASE}/api/donors/upload-card`;
  const resp = await fetch(url, { method: "POST", body: formData });
  if (!resp.ok) throw new Error(`Upload failed: ${resp.status}`);
  return resp.json() as Promise<CardOcrResult>;
}

// ── Telegram Login ─────────────────────────────────────────────────────────────
export async function telegramLogin(token: string): Promise<{ access_token: string; donor_id: string }> {
  return apiFetch<{ access_token: string; donor_id: string }>(`/api/auth/telegram-login?token=${encodeURIComponent(token)}`);
}

// ── Feature 1: Donor Profile Update ───────────────────────────────────────────
export async function updateDonorProfile(id: string, data: { name?: string; phone?: string; city?: string; preferred_language?: string }): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>(`/api/donors/${id}/profile`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

// ── Feature 2: Patient Profile Update ─────────────────────────────────────────
export async function updatePatientProfile(id: string, data: { name?: string; phone?: string; hospital?: string; ward?: string }): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>(`/api/patients/${id}/profile`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

// ── Feature 4: Set Next Transfusion Date ──────────────────────────────────────
export async function setNextTransfusion(id: string, date: string): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>(`/api/patients/${id}/set-next-transfusion`, {
    method: "POST",
    body: JSON.stringify({ date }),
  });
}

// ── Feature 5: Blood Bridge Visualization ─────────────────────────────────────
export interface BridgeMember {
  donor_id?: string;
  patient_id?: string;
  donor_name?: string;
  patient_name?: string;
  blood_type: string;
  antigen_score: number;
  joined_at?: string;
}

export async function getDonorBridges(id: string): Promise<BridgeMember[]> {
  return apiFetch<BridgeMember[]>(`/api/donors/${id}/bridges`);
}

export async function getPatientBridges(id: string): Promise<BridgeMember[]> {
  return apiFetch<BridgeMember[]>(`/api/patients/${id}/bridges`);
}

// ── Feature: Patient Health Record Update ─────────────────────────────────────
export async function updatePatientHealth(id: string, data: {
  hemoglobin?: number;
  antibody_kell?: boolean;
  antibody_duffy?: boolean;
  antibody_kidd?: boolean;
  antibody_rh_e?: boolean;
  antibody_rh_c?: boolean;
  antibody_mns?: boolean;
}): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>(`/api/patients/${id}/health`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

// ── Admin CRUD: Delete Donors/Patients + Manage Bridges ───────────────────────
export async function adminDeleteDonor(id: string): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>(`/api/admin/donors/${id}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
}

export async function adminDeletePatient(id: string): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>(`/api/admin/patients/${id}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
}

export async function adminCreateBridge(patientId: string, donorId: string): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>("/api/admin/bridges", {
    method: "POST",
    body: JSON.stringify({ patient_id: patientId, donor_id: donorId }),
    headers: getAuthHeaders(),
  });
}

export async function adminDeleteBridge(patientId: string, donorId: string): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>(`/api/admin/bridges/${patientId}/${donorId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
}

export interface BridgeMembership {
  bridge_id: string;
  donor_id: string;
  antigen_score?: number;
  created_at?: string;
}

export async function adminGetBridges(): Promise<BridgeMembership[]> {
  return apiFetch<BridgeMembership[]>("/api/admin/bridges", {
    headers: getAuthHeaders(),
  });
}
