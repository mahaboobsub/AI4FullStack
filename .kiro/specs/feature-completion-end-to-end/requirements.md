# Requirements Document

## Introduction

This feature wires up every remaining 🟡 (partial) and 🔴 (missing) capability identified in the BloodBridge AI feature audit (`FEATURES_DEEP_DIVE.md`, `PRESENTATION.md`) so that every backend endpoint has a working frontend surface and every frontend component is functional end-to-end. The work is overwhelmingly frontend (new pages, panels, drawers, file inputs, calls into `lib/api.ts`), with one new backend endpoint (`POST /api/donors/upload-card`) and six new frontend API client methods. Out of scope: SMS/Twilio fallback, LoRa hardware, cloud deployment, Phase 2 antigen phenotyping, and any change to `.env`, MCP, the `ChatBedrockConverse` LLM provider, the current TRAI test window, or the AI-call monitor timeout.

## Glossary

- **DonorPortal_UI**: The donor-facing portal page at `pages/DonorPortal.tsx`.
- **Admin_UI**: The staff/admin dashboard page at `pages/dashboard/Admin.tsx`.
- **SignUp_UI**: The registration page at `pages/SignUp.tsx`.
- **Map_UI**: The blood-bank map page at `pages/dashboard/Map.tsx`.
- **Emergency_UI**: The emergency dashboard page at `pages/dashboard/Emergency.tsx`.
- **TelegramLogin_UI**: A new page `pages/TelegramLogin.tsx` mounted at the route `/donor/telegram-login`.
- **API_Client**: The frontend HTTP wrapper at `BloodBridge_AI_frontend/artifacts/bloodbridge/src/lib/api.ts`.
- **BloodBridge_API**: The FastAPI backend rooted at `BloodBridge_AI_Backend/main.py`.
- **OCR_Service**: The Textract-backed helper `extract_blood_type_from_image` in `BloodBridge_AI_Backend/services/ocr_service.py`.
- **Privacy_Tab**: A new section/tab inside DonorPortal_UI titled "Privacy & Consent".
- **Eligibility_Card**: A new card on DonorPortal_UI showing donation-eligibility status.
- **Leaderboard_View**: A new section on DonorPortal_UI rendering the city leaderboard.
- **Trace_Drawer**: A slide-out drawer on Emergency_UI showing per-emergency agentic trace data.
- **LoRa_Panel**: A new panel on Admin_UI showing LoRa gateway connectivity.
- **Schedule_Widget**: A new list/calendar widget on Admin_UI showing upcoming transfusion schedule entries.
- **Config_Editor**: A new form on Admin_UI for editing agent runtime config via `PUT /api/admin/config`.
- **Bulk_Import_Panel**: A new admin-only file-upload panel on Admin_UI for CSV donor import.
- **Card_Upload_Field**: A new optional file input on SignUp_UI for blood-card image upload.
- **Refresh_Button**: A new button on Map_UI that triggers an e-RaktKosh inventory refresh.
- **Donor_Role**: The "donor" value of the role selector in SignUp_UI.
- **Auth_Token**: The JWT stored at `localStorage.auth_token` after a successful login.
- **Donor_Id**: The string donor identifier stored at `localStorage.donor_id` after login.

## Requirements

### Requirement 1: DPDP Privacy Tab on Donor Portal

**User Story:** As a donor, I want a Privacy & Consent area inside my portal, so that I can see what I have consented to and exercise my DPDP 2023 rights to revoke consent, export my data, and delete my account.

#### Acceptance Criteria

1. WHEN a donor opens DonorPortal_UI, THE DonorPortal_UI SHALL render the Privacy_Tab as a navigable section that does not displace existing portal content.
2. WHEN the Privacy_Tab is opened for the first time in a session, THE DonorPortal_UI SHALL call `getConsentSummary(donorId)` from API_Client and display each consent key with its current state ("granted", "revoked", or "not_given").
3. THE Privacy_Tab SHALL render a "Revoke" control for each consent key returned by `getConsentSummary` whose state is "granted".
4. WHEN a donor activates the "Revoke" control for a specific consent key, THE DonorPortal_UI SHALL call `revokeConsent(donorId, consentType)` from API_Client with that exact consent key.
5. WHEN `revokeConsent` returns success, THE DonorPortal_UI SHALL re-render the affected consent row with state "revoked" and SHALL NOT remove the row from the list.
6. THE Privacy_Tab SHALL render an "Export My Data" control and a "Delete My Account" control.
7. WHEN a donor activates "Export My Data", THE DonorPortal_UI SHALL call `exportDonorData(donorId)` from API_Client and SHALL deliver the returned JSON payload to the donor as a downloadable file named `donor-data-{donorId}.json`.
8. WHEN a donor activates "Delete My Account", THE DonorPortal_UI SHALL display a confirmation prompt that requires an explicit second action before any deletion request is sent.
9. WHEN the donor confirms account deletion in the prompt, THE DonorPortal_UI SHALL call `eraseDonorData(donorId)` from API_Client.
10. WHEN `eraseDonorData` returns success, THE DonorPortal_UI SHALL clear Auth_Token and Donor_Id from localStorage and SHALL navigate to the public landing route.
11. IF any of `getConsentSummary`, `revokeConsent`, `exportDonorData`, or `eraseDonorData` returns an error, THEN THE DonorPortal_UI SHALL display an inline error message in the Privacy_Tab and SHALL preserve the previously rendered consent state.

### Requirement 2: Bulk CSV Donor Import on Admin

**User Story:** As an admin, I want to upload a CSV file of donors from the admin dashboard, so that I can onboard donor batches without leaving the UI.

#### Acceptance Criteria

1. WHILE the current user has the admin role, THE Admin_UI SHALL render the Bulk_Import_Panel.
2. IF the current user does not have the admin role, THEN THE Admin_UI SHALL NOT render the Bulk_Import_Panel.
3. THE Bulk_Import_Panel SHALL accept exactly one file at a time via a file input restricted to the `.csv` extension.
4. THE Bulk_Import_Panel SHALL render a checkbox labelled "Grant consent on import" that is checked by default.
5. WHEN the admin selects a file and activates the "Upload" control, THE Admin_UI SHALL POST that file as `multipart/form-data` to `/api/donors/bulk-import-csv` with the query parameter `grant_consent` set to the checkbox state.
6. THE Bulk_Import_Panel SHALL include the staff token (header `X-Staff-Token`) on the upload request using the same header value used by other admin calls in API_Client.
7. WHEN the upload returns a 2xx response, THE Bulk_Import_Panel SHALL display the response summary (counts of inserted, skipped, and failed rows).
8. IF the upload returns a 4xx or 5xx response, THEN THE Bulk_Import_Panel SHALL display the response body's error detail and SHALL NOT clear the selected file.
9. WHILE an upload request is in flight, THE Bulk_Import_Panel SHALL disable the "Upload" control.

### Requirement 3: Telegram Deep-Link Landing Page

**User Story:** As a donor who tapped a one-time login link from the Telegram bot, I want a landing page that completes my login automatically, so that I am taken straight into my portal without re-typing credentials.

#### Acceptance Criteria

1. THE frontend router SHALL register the path `/donor/telegram-login` and bind it to TelegramLogin_UI.
2. WHEN TelegramLogin_UI mounts, THE TelegramLogin_UI SHALL read the `token` query parameter from the URL.
3. IF the `token` query parameter is absent or empty, THEN THE TelegramLogin_UI SHALL display an error message stating the link is invalid and SHALL NOT call any backend endpoint.
4. WHEN a non-empty `token` is present, THE TelegramLogin_UI SHALL call `GET /api/auth/telegram-login?token={token}` exactly once per mount.
5. WHEN the `GET /api/auth/telegram-login` response is successful, THE TelegramLogin_UI SHALL store the response's JWT in `localStorage.auth_token` and the response's donor id in `localStorage.donor_id`.
6. WHEN Auth_Token and Donor_Id have been written to localStorage, THE TelegramLogin_UI SHALL navigate to `/donor`.
7. IF the `GET /api/auth/telegram-login` call returns an error, THEN THE TelegramLogin_UI SHALL display the error message and SHALL render a "Back to Login" link to `/login`.
8. WHILE the login call is in flight, THE TelegramLogin_UI SHALL render a loading indicator and SHALL NOT navigate.

### Requirement 4: Blood Card OCR Upload at Sign-Up

**User Story:** As a new donor, I want to upload a photo of my blood-group card at sign-up, so that the system can pre-fill my blood type for me.

#### Acceptance Criteria

1. WHILE the role selector in SignUp_UI is set to Donor_Role, THE SignUp_UI SHALL render the Card_Upload_Field labelled "Upload Blood Card (Optional)".
2. IF the role selector in SignUp_UI is not set to Donor_Role, THEN THE SignUp_UI SHALL NOT render the Card_Upload_Field.
3. THE Card_Upload_Field SHALL accept exactly one image file restricted to MIME types `image/jpeg`, `image/png`, and `image/webp`.
4. THE BloodBridge_API SHALL expose `POST /api/donors/upload-card` that accepts a single `multipart/form-data` field named `file` containing the image.
5. WHEN `POST /api/donors/upload-card` receives a request, THE BloodBridge_API SHALL invoke `extract_blood_type_from_image` from OCR_Service with the uploaded bytes.
6. WHEN `extract_blood_type_from_image` returns successfully, THE BloodBridge_API SHALL respond with a JSON body containing the keys `blood_group` and `name` whose values come from the OCR result.
7. IF `extract_blood_type_from_image` raises or returns no recognisable blood group, THEN THE BloodBridge_API SHALL respond with HTTP 422 and a JSON body containing a `detail` field explaining the failure.
8. WHEN the upload request returns success, THE SignUp_UI SHALL set the form's `bloodGroup` select value to the returned `blood_group` if it is a valid option.
9. WHEN the upload request returns success and the response includes a non-empty `name`, THE SignUp_UI SHALL pre-fill the form's name field with that value if and only if the name field is currently empty.
10. WHILE a card upload request is in flight, THE SignUp_UI SHALL render an inline progress indicator next to the Card_Upload_Field.
11. IF a card upload returns an error response, THEN THE SignUp_UI SHALL display the error inline beneath the Card_Upload_Field and SHALL NOT modify any form field.

### Requirement 5: Donor Eligibility Card on Donor Portal

**User Story:** As a donor, I want to see when I am next eligible to donate, so that I know when I can respond to alerts.

#### Acceptance Criteria

1. WHEN DonorPortal_UI mounts, THE DonorPortal_UI SHALL call `getDonorEligibility(donorId)` from API_Client exactly once.
2. WHEN `getDonorEligibility` returns `eligible: true`, THE Eligibility_Card SHALL display "Eligible to donate now".
3. WHEN `getDonorEligibility` returns `eligible: false` and `days_until_eligible` is a non-null integer, THE Eligibility_Card SHALL display "Eligible to donate again on {date}" where `{date}` is today's date plus `days_until_eligible` days, formatted in the user's locale.
4. WHEN `getDonorEligibility` returns `eligible: false` and `reason` is non-null, THE Eligibility_Card SHALL display the `reason` string as secondary text.
5. IF `getDonorEligibility` returns an error, THEN THE Eligibility_Card SHALL display "Eligibility unavailable" and SHALL NOT crash the rest of the portal.

### Requirement 6: Donor Leaderboard View on Donor Portal

**User Story:** As a donor, I want to see the top donors in my city, so that I can see my rank and stay engaged.

#### Acceptance Criteria

1. WHEN DonorPortal_UI mounts and a city is known for the donor, THE DonorPortal_UI SHALL call `getLeaderboard(city)` from API_Client.
2. WHEN `getLeaderboard` returns a non-empty list, THE Leaderboard_View SHALL render up to ten entries in ascending rank order, each row showing rank, name, lives saved, donation count, and badges.
3. WHEN `getLeaderboard` returns an empty list, THE Leaderboard_View SHALL display "No leaderboard data available for {city}".
4. IF `getLeaderboard` returns an error, THEN THE Leaderboard_View SHALL display "Leaderboard unavailable" and SHALL NOT crash the rest of the portal.
5. THE Leaderboard_View SHALL highlight the row whose donor identity matches the currently logged-in donor when such a row exists in the returned list.

### Requirement 7: Per-Emergency Agent Trace Drawer

**User Story:** As staff viewing an emergency on the dashboard, I want to inspect the agentic trace for that specific emergency, so that I can debug coordination and prove autonomy.

#### Acceptance Criteria

1. THE API_Client SHALL expose a function `getEmergencyTrace(id: string): Promise<AgentTrace>` that performs a `GET` request to `/api/emergencies/{id}/trace`.
2. THE Emergency_UI SHALL render a "View Trace" control on each emergency card.
3. WHEN staff activates the "View Trace" control on a specific emergency card, THE Emergency_UI SHALL call `getEmergencyTrace(id)` for that emergency's id and SHALL open the Trace_Drawer.
4. THE Trace_Drawer SHALL display the trace's `request_id`, `outcome`, `node_count`, `total_ms`, and an ordered list of nodes showing each `name`, `status`, and `duration_ms`.
5. WHILE a trace request is in flight, THE Trace_Drawer SHALL render a loading state.
6. IF `getEmergencyTrace` returns an error, THEN THE Trace_Drawer SHALL display the error message and SHALL keep the drawer open until the staff member dismisses it.
7. WHEN the staff member dismisses the Trace_Drawer, THE Emergency_UI SHALL hide the drawer without unmounting the underlying emergency list.

### Requirement 8: e-RaktKosh Inventory Refresh on Map

**User Story:** As staff using the map, I want a Refresh button that re-pulls e-RaktKosh inventory, so that I can see current stock without restarting the app.

#### Acceptance Criteria

1. THE API_Client SHALL expose a function `refreshBloodBanks(): Promise<{ status: string; message?: string }>` that performs a `POST` request to `/api/blood-banks/refresh`.
2. THE Map_UI SHALL render a Refresh_Button labelled "Refresh inventory".
3. WHEN staff activates the Refresh_Button, THE Map_UI SHALL call `refreshBloodBanks` exactly once and SHALL disable the Refresh_Button until the call completes.
4. WHEN `refreshBloodBanks` returns success, THE Map_UI SHALL re-fetch the blood-bank list for the currently displayed city and SHALL display a "Refreshed" toast.
5. IF `refreshBloodBanks` returns an error, THEN THE Map_UI SHALL display the error message in a toast and SHALL re-enable the Refresh_Button without altering map state.

### Requirement 9: LoRa Connectivity Panel on Admin

**User Story:** As an admin, I want to see LoRa gateway status at a glance, so that I know whether offline-queue donors are reaching the system.

#### Acceptance Criteria

1. THE API_Client SHALL expose a function `getLoraStatus(): Promise<{ queue_depth: number; last_packet_at: string | null; gateway_online: boolean }>` that performs a `GET` request to `/api/lora/status`.
2. WHEN Admin_UI mounts, THE Admin_UI SHALL call `getLoraStatus` and SHALL render the LoRa_Panel with `queue_depth`, `last_packet_at`, and `gateway_online`.
3. WHILE Admin_UI is mounted, THE Admin_UI SHALL re-poll `getLoraStatus` no more often than once every 30 seconds.
4. IF `getLoraStatus` returns an error, THEN THE LoRa_Panel SHALL display "LoRa status unavailable" and SHALL preserve any previously rendered values until the next successful poll.

### Requirement 10: Schedule Calendar Widget on Admin

**User Story:** As an admin, I want to see upcoming scheduled transfusions, so that I can plan donor outreach ahead of time.

#### Acceptance Criteria

1. THE API_Client SHALL expose a function `getScheduleEntries(daysAhead?: number): Promise<ScheduleEntry[]>` that performs a `GET` request to `/api/schedule` and forwards `daysAhead` as the `days_ahead` query parameter when provided.
2. WHEN Admin_UI mounts, THE Admin_UI SHALL call `getScheduleEntries` and SHALL render the Schedule_Widget with the returned entries grouped or sorted by `scheduled_date` ascending.
3. THE Schedule_Widget SHALL show, for each entry, the `scheduled_date`, `patient_id`, `blood_type`, `hospital`, and `status`.
4. WHEN `getScheduleEntries` returns an empty list, THE Schedule_Widget SHALL display "No scheduled transfusions in the selected window".
5. IF `getScheduleEntries` returns an error, THEN THE Schedule_Widget SHALL display "Schedule unavailable" and SHALL NOT crash the rest of Admin_UI.

### Requirement 11: Agent Config Editor on Admin

**User Story:** As an admin, I want to edit agent runtime configuration from the dashboard, so that I can tune coordination behaviour without redeploying.

#### Acceptance Criteria

1. WHEN Admin_UI mounts, THE Admin_UI SHALL call `getAgentConfig()` from API_Client and SHALL pre-fill the Config_Editor form with the returned values.
2. THE Config_Editor SHALL render editable form controls for `coordination_timeout_mins`, `retry_limit`, `safe_calling_hours.start`, and `safe_calling_hours.end`, and a multi-select control for `channel_sequence`.
3. THE Config_Editor SHALL render `app_env` and `demo_mock_mode` as read-only fields.
4. WHILE the Config_Editor form has unsaved changes, THE Config_Editor SHALL display a "Save" control in an enabled state.
5. WHEN the admin activates "Save", THE Admin_UI SHALL call `updateAgentConfig` from API_Client with the full edited config object.
6. WHEN `updateAgentConfig` returns success, THE Config_Editor SHALL display a "Configuration saved" confirmation and SHALL clear the unsaved-changes state.
7. IF `updateAgentConfig` returns an error, THEN THE Config_Editor SHALL display the error message and SHALL keep the unsaved-changes state intact.
8. IF `coordination_timeout_mins` is not a positive integer or `retry_limit` is not a non-negative integer at the time of "Save", THEN THE Config_Editor SHALL block the call and SHALL display a per-field validation error.
