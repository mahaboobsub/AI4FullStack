import sys
import os
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, date, timedelta

# Add backend root to path
backend_path = r"c:\Users\Lenovo\Downloads\BloodBridge-AI (1)\BloodBridge_AI_Backend"
sys.path.append(backend_path)

from fastapi.testclient import TestClient
from main import app

class TestPhase6API(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        # Reset database singletons to guarantee create_client is called when get_supabase_admin() is executed
        import core.database
        core.database._supabase_client = None
        core.database._supabase_admin_client = None

    @patch('core.database.create_client')
    @patch('core.ws_manager.ws_manager.broadcast', new_callable=AsyncMock)
    @patch('agents.graph.run_emergency_pipeline')
    async def test_emergency_endpoints(self, mock_pipeline, mock_broadcast, mock_create_client):
        # Setup mocks
        mock_supabase = MagicMock()
        mock_create_client.return_value = mock_supabase
        
        # Mock active emergencies response
        mock_res = MagicMock()
        mock_res.data = [{
            "request_id": "REQ-12345",
            "patient_id": "P-100",
            "blood_type": "O+",
            "city": "Hyderabad",
            "priority": "CRITICAL",
            "urgency_score": 8.5,
            "hospital_name": "Apollo",
            "ward": "ICU",
            "status": "IN_PROGRESS",
            "created_at": "2026-06-04T12:00:00Z"
        }]
        
        mock_chain_res = MagicMock()
        mock_chain_res.data = [{
            "donor_id": "D-1",
            "donor_name": "Suresh",
            "chain_position": 1,
            "status": "CONFIRMED",
            "antigen_score": 0.9,
            "alerted_at": "2026-06-04T12:05:00Z",
            "confirmed_at": "2026-06-04T12:10:00Z"
        }]
        
        # Make table().select().eq().execute() chainable
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_res
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_chain_res
        
        # Test GET /api/emergencies
        response = self.client.get("/api/emergencies")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["request_id"], "REQ-12345")
        self.assertEqual(len(data[0]["chain"]), 1)
        
        # Test GET /api/emergencies/{id}
        response = self.client.get("/api/emergencies/REQ-12345")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["request_id"], "REQ-12345")
        
        # Mock POST /api/emergencies
        # Mock patient validation query
        mock_patient_res = MagicMock()
        mock_patient_res.data = [{"patient_id": "P-100"}]
        
        mock_insert_res = MagicMock()
        mock_insert_res.data = [{"request_id": "REQ-12345"}]
        
        # Modify mock table behavior based on table name
        def mock_table(name):
            t_mock = MagicMock()
            if name == "patients":
                t_mock.select.return_value.eq.return_value.execute.return_value = mock_patient_res
            elif name == "emergency_requests":
                # select for idempotency check: returns empty data (no duplicate)
                mock_idempotency_res = MagicMock()
                mock_idempotency_res.data = []
                t_mock.select.return_value.eq.return_value.execute.return_value = mock_idempotency_res
                t_mock.insert.return_value.execute.return_value = mock_insert_res
            return t_mock
            
        mock_supabase.table.side_effect = mock_table
        
        payload = {
            "patient_id": "P-100",
            "blood_type": "O+",
            "city": "Hyderabad",
            "ward": "ICU",
            "hospital": "Apollo"
        }
        
        response = self.client.post("/api/emergencies", json=payload, headers={"X-Idempotency-Key": "test-key-123"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["requestId"], "REQ-12345")
        
        # Test POST /api/emergencies/{id}/confirm
        mock_confirm_req_res = MagicMock()
        mock_confirm_req_res.data = [{"status": "IN_PROGRESS"}]
        
        def mock_table_confirm(name):
            t_mock = MagicMock()
            if name == "emergency_requests":
                t_mock.select.return_value.eq.return_value.execute.return_value = mock_confirm_req_res
                t_mock.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
            elif name == "blood_chains":
                t_mock.update.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
            return t_mock
            
        mock_supabase.table.side_effect = mock_table_confirm
        
        response = self.client.post("/api/emergencies/REQ-12345/confirm")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        
        # Test GET /api/emergencies/{id}/chain
        def mock_table_chain(name):
            t_mock = MagicMock()
            if name == "blood_chains":
                t_mock.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_chain_res
            return t_mock
        mock_supabase.table.side_effect = mock_table_chain
        
        response = self.client.get("/api/emergencies/REQ-12345/chain")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        
        # Test GET /api/emergencies/{id}/trace
        mock_trace_res = MagicMock()
        mock_trace_res.data = [{
            "request_id": "REQ-12345",
            "patient_id": "P-100",
            "started_at": "2026-06-04T12:00:00Z",
            "outcome": "SUCCESS",
            "node_count": 3,
            "total_ms": 1200,
            "nodes_json": [{"name": "intake", "status": "success", "duration_ms": 200}]
        }]
        
        def mock_table_trace(name):
            t_mock = MagicMock()
            if name == "agent_traces":
                t_mock.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_trace_res
            return t_mock
        mock_supabase.table.side_effect = mock_table_trace
        
        response = self.client.get("/api/emergencies/REQ-12345/trace")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["request_id"], "REQ-12345")
        self.assertEqual(len(response.json()["nodes"]), 1)

    @patch('core.database.create_client')
    @patch('services.consent_service.consent_service')
    @patch('services.voice_service.make_vapi_call', new_callable=AsyncMock)
    @patch('services.telegram_bot.send_telegram_message', new_callable=AsyncMock)
    async def test_donor_endpoints(self, mock_telegram, mock_voice, mock_consent, mock_create_client):
        mock_supabase = MagicMock()
        mock_create_client.return_value = mock_supabase
        
        # Mock GET /api/donors
        mock_donors_res = MagicMock()
        mock_donors_res.data = [{
            "donor_id": "D-1",
            "name": "Amit Sharma",
            "blood_type": "B+",
            "city": "Hyderabad",
            "kell_negative": True,
            "churn_score": 0.15,
            "churn_risk": "LOW",
            "donation_count": 5,
            "lives_saved": 5,
            "last_donation_date": (date.today() - timedelta(days=60)).isoformat(),
            "response_rate": 0.85,
            "preferred_language": "Hindi",
            "telegram_chat_id": "@amit",
            "is_active": True,
            "medical_hold": False,
            "hemoglobin": 13.5
        }]
        
        mock_mem_res = MagicMock()
        mock_mem_res.data = [{"donor_id": "D-1", "badges": ["life_saver"]}]
        
        def mock_table_donors(name):
            t_mock = MagicMock()
            if name == "donors":
                t_mock.select.return_value.execute.return_value = mock_donors_res
                t_mock.select.return_value.eq.return_value.execute.return_value = mock_donors_res
            elif name == "donor_memory":
                t_mock.select.return_value.execute.return_value = mock_mem_res
                t_mock.select.return_value.eq.return_value.execute.return_value = mock_mem_res
            return t_mock
            
        mock_supabase.table.side_effect = mock_table_donors
        
        response = self.client.get("/api/donors")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["donor_id"], "D-1")
        self.assertEqual(response.json()[0]["badges"], ["life_saver"])
        
        # Test GET /api/donors/{id}
        response = self.client.get("/api/donors/D-1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["donor_id"], "D-1")
        
        # Test GET /api/donors/{id}/eligibility
        response = self.client.get("/api/donors/D-1/eligibility")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["eligible"])
        
        # Test POST /api/donors/{id}/voice
        mock_donor_voice = MagicMock()
        mock_donor_voice.data = [{
            "donor_id": "D-1",
            "name": "Amit Sharma",
            "phone": "+919876543210",
            "blood_type": "B+"
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_donor_voice
        
        mock_voice.return_value = {"status": "INITIATED", "call_id": "call-123"}
        response = self.client.post("/api/donors/D-1/voice")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["callSid"], "call-123")
        
        # Test POST /api/donors/{id}/outreach
        mock_donor_outreach = MagicMock()
        mock_donor_outreach.data = [{
            "name": "Amit Sharma",
            "preferred_language": "Hindi",
            "telegram_chat_id": "123456789"
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_donor_outreach
        mock_telegram.return_value = True
        
        response = self.client.post("/api/donors/D-1/outreach")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["messageId"].startswith("MSG-D-1"))
        
        # Test GET /api/donors/{id}/consent
        mock_consent.get_consent_summary = AsyncMock(return_value={"data_storage": True, "outreach_telegram": True})
        response = self.client.get("/api/donors/D-1/consent")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["data_storage"])
        
        # Test POST /api/donors/{id}/consent/revoke
        mock_consent.revoke_consent = AsyncMock(return_value=True)
        response = self.client.post("/api/donors/D-1/consent/revoke", json={"consent_type": "outreach_telegram"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        
        # Test DELETE /api/donors/{id}/data
        mock_consent.erase_donor_data = AsyncMock(return_value={"success": True})
        response = self.client.delete("/api/donors/D-1/data")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        
        # Test GET /api/donors/{id}/my-data
        mock_consent.export_donor_data = AsyncMock(return_value={"donor": {"name": "Amit"}})
        response = self.client.get("/api/donors/D-1/my-data")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["donor"]["name"], "Amit")
        
        # Test POST /api/donors/bulk-import
        mock_dup_res = MagicMock()
        mock_dup_res.data = []
        mock_insert_d_res = MagicMock()
        mock_insert_d_res.data = [{"donor_id": "D-NEW"}]
        
        def mock_table_import(name):
            t_mock = MagicMock()
            if name == "donors":
                t_mock.select.return_value.eq.return_value.execute.return_value = mock_dup_res
                t_mock.insert.return_value.execute.return_value = mock_insert_d_res
            elif name == "donor_memory":
                t_mock.insert.return_value.execute.return_value = MagicMock(data=[])
            return t_mock
        mock_supabase.table.side_effect = mock_table_import
        mock_consent.grant_consent = AsyncMock(return_value=True)
        
        bulk_payload = {
            "donors": [{
                "name": "New Donor",
                "blood_type": "O-",
                "city": "Mumbai",
                "phone": "+919999999999",
                "telegram_chat_id": "@new_donor",
                "kell_negative": False,
                "preferred_language": "English"
            }]
        }
        response = self.client.post("/api/donors/bulk-import", json=bulk_payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["imported_count"], 1)

    @patch('core.database.create_client')
    async def test_patient_endpoints(self, mock_create_client):
        mock_supabase = MagicMock()
        mock_create_client.return_value = mock_supabase
        
        mock_patient = MagicMock()
        mock_patient.data = [{
            "patient_id": "P-100",
            "name": "Karan Sharma",
            "age": 8,
            "blood_type": "B+",
            "hospital": "KIMS",
            "ward": "Day Care",
            "transfusion_count": 50,
            "next_transfusion_due": "2026-06-15",
            "hemoglobin": 5.2,
            "status": "STABLE",
            "kell_negative": True,
            "antibody_kell": True,
            "antibody_duffy": False,
            "antibody_kidd": False,
            "antibody_rh_e": False,
            "antibody_rh_c": False,
            "antibody_mns": False
        }]
        
        # Mock active request
        mock_req_res = MagicMock()
        mock_req_res.data = [{"request_id": "REQ-12345"}]
        
        # Mock linked donors in chain
        mock_chain_res = MagicMock()
        mock_chain_res.data = [{
            "donor_id": "D-1",
            "donor_name": "Amit Sharma",
            "status": "CONFIRMED",
            "antigen_score": 0.95
        }]
        
        # Mock donor profile for linked donor
        mock_d_res = MagicMock()
        mock_d_res.data = [{"donation_count": 10}]
        
        # Mock donor memory for linked donor badges
        mock_mem_res = MagicMock()
        mock_mem_res.data = [{"badges": ["life_saver", "blood_hero"]}]
        
        # Mock transfusion history
        mock_history_res = MagicMock()
        mock_history_res.data = [{
            "scheduled_date": "2026-05-15",
            "hospital": "KIMS",
            "blood_type": "B+",
            "request_id": "REQ-10000",
            "status": "COMPLETED"
        }]
        
        mock_completed_chain_res = MagicMock()
        mock_completed_chain_res.data = [{"donor_name": "Amit Sharma"}]
        
        def mock_table_patients(name):
            t_mock = MagicMock()
            if name == "patients":
                t_mock.select.return_value.eq.return_value.execute.return_value = mock_patient
            elif name == "emergency_requests":
                t_mock.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_req_res
            elif name == "blood_chains":
                t_mock.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_chain_res
                t_mock.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_completed_chain_res
            elif name == "donors":
                t_mock.select.return_value.eq.return_value.execute.return_value = mock_d_res
            elif name == "donor_memory":
                t_mock.select.return_value.eq.return_value.execute.return_value = mock_mem_res
            elif name == "transfusion_schedule":
                t_mock.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = mock_history_res
            return t_mock
            
        mock_supabase.table.side_effect = mock_table_patients
        
        response = self.client.get("/api/patients/P-100")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["patient_id"], "P-100")
        self.assertIn("Anti-Kell", data["antibody_flags"])
        self.assertEqual(len(data["linked_donors"]), 1)
        self.assertEqual(data["linked_donors"][0]["badges"], ["life_saver", "blood_hero"])
        self.assertEqual(len(data["transfusion_history"]), 1)
        self.assertEqual(data["transfusion_history"][0]["donor_name"], "Amit Sharma")

    @patch('api.blood_banks.get_driver')
    async def test_blood_banks_endpoints(self, mock_get_driver):
        # Mock Neo4j session and record
        mock_session = AsyncMock()
        mock_driver = MagicMock()
        mock_driver.session.return_value.__aenter__.return_value = mock_session
        mock_get_driver.return_value = mock_driver
        
        mock_record = MagicMock()
        mock_node = {
            "id": "BB-KIMS",
            "name": "KIMS Blood Bank",
            "city": "Hyderabad",
            "units_b_pos": 10,
            "units_o_pos": 5,
            "contact": "12345",
            "lat": 17.4480,
            "lng": 78.4982,
            "distance_km": 1.5,
            "drive_min": 5
        }
        mock_record.__getitem__.return_value = mock_node
        
        mock_result = AsyncMock()
        mock_result.__aiter__.return_value = [mock_record].__iter__()
        mock_session.run.return_value = mock_result
        
        response = self.client.get("/api/blood-banks?city=Hyderabad")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], "BB-KIMS")
        self.assertEqual(data[0]["units"]["B+"], 10)
        
        response = self.client.post("/api/blood-banks/refresh")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

    @patch('core.database.create_client')
    @patch('api.admin.check_neo4j')
    @patch('httpx.AsyncClient')
    @patch('data.generate_synthetic.train_and_save_models')
    async def test_admin_endpoints(self, mock_train, mock_http, mock_check_neo4j, mock_create_client):
        mock_supabase = MagicMock()
        mock_create_client.return_value = mock_supabase
        
        mock_check_neo4j.return_value = True
        
        mock_count = MagicMock()
        mock_count.count = 500
        mock_supabase.table.return_value.select.return_value.limit.return_value.execute.return_value = mock_count
        
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_client = MagicMock()
        mock_client.__aenter__.return_value.get.return_value = mock_resp
        mock_http.return_value = mock_client
        
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        health_data = response.json()
        self.assertTrue(any(s["service"] == "Neo4j Aura" and s["status"] == "online" for s in health_data))
        self.assertTrue(any(s["service"] == "Supabase" and s["status"] == "online" for s in health_data))
        
        mock_trace_db = MagicMock()
        mock_trace_db.data = [{
            "request_id": "REQ-12345",
            "patient_id": "P-100",
            "started_at": "2026-06-04T12:00:00Z",
            "outcome": "SUCCESS",
            "node_count": 3,
            "total_ms": 800,
            "nodes_json": []
        }]
        mock_supabase.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value = mock_trace_db
        
        response = self.client.get("/api/traces")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["request_id"], "REQ-12345")
        
        # Test GET /api/analytics
        mock_total = MagicMock()
        mock_total.count = 100
        
        mock_active = MagicMock()
        mock_active.count = 80
        
        mock_risk = MagicMock()
        mock_risk.count = 5
        
        mock_rates = MagicMock()
        mock_rates.data = [{"response_rate": 0.8}, {"response_rate": 0.9}]
        
        mock_month = MagicMock()
        mock_month.count = 15
        
        mock_city = MagicMock()
        mock_city.data = [{"city": "Hyderabad", "lives_saved": 10}, {"city": "Mumbai", "lives_saved": 5}]
        
        class ChainRecorder:
            def __init__(self, table_name):
                self.table_name = table_name
                self.calls = []
                
            def select(self, *args, **kwargs):
                self.calls.append(("select", args, kwargs))
                return self
                
            def eq(self, *args, **kwargs):
                self.calls.append(("eq", args, kwargs))
                return self
                
            def in_(self, *args, **kwargs):
                self.calls.append(("in_", args, kwargs))
                return self
                
            def gte(self, *args, **kwargs):
                self.calls.append(("gte", args, kwargs))
                return self
                
            def execute(self):
                has_eq_active = any(c[0] == "eq" and c[1][0] == "is_active" for c in self.calls)
                has_in_risk = any(c[0] == "in_" and c[1][0] == "churn_risk" for c in self.calls)
                has_gte_date = any(c[0] == "gte" and c[1][0] == "last_donation_date" for c in self.calls)
                has_lives_saved = any(c[0] == "select" and "lives_saved" in c[1][0] for c in self.calls)
                has_response_rate = any(c[0] == "select" and "response_rate" in c[1][0] for c in self.calls)
                
                if has_lives_saved:
                    return mock_city
                elif has_gte_date:
                    return mock_month
                elif has_in_risk:
                    return mock_risk
                elif has_eq_active:
                    if has_response_rate:
                        return mock_rates
                    return mock_active
                else:
                    return mock_total
                    
        mock_supabase.table.side_effect = lambda name: ChainRecorder(name)
        
        response = self.client.get("/api/analytics")
        self.assertEqual(response.status_code, 200)
        analytics_data = response.json()
        self.assertEqual(analytics_data["total_donors"], 100)
        self.assertEqual(analytics_data["active_donors"], 80)
        self.assertEqual(analytics_data["active_pct"], 80.0)
        self.assertEqual(analytics_data["at_risk_count"], 5)
        self.assertEqual(analytics_data["donated_this_month"], 15)
        self.assertEqual(analytics_data["by_city"][0]["city"], "Hyderabad")
        
        response = self.client.post("/api/models/retrain")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["jobId"].startswith("JOB-"))
        
        response = self.client.get("/api/config")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["coordination_timeout_mins"], 7)
        
        response = self.client.put("/api/config", json={"timeout": 10})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        
        mock_staff_res = MagicMock()
        mock_staff_res.data = [{
            "telegram_username": "@amit_coord",
            "hospital": "Apollo",
            "role": "Coordinator",
            "added_at": "2026-06-01T12:00:00Z"
        }]
        
        def mock_table_staff(name):
            t_mock = MagicMock()
            if name == "staff":
                t_mock.select.return_value.execute.return_value = mock_staff_res
                t_mock.insert.return_value.execute.return_value = MagicMock(data=[])
                t_mock.delete.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
            return t_mock
        mock_supabase.table.side_effect = mock_table_staff
        
        response = self.client.get("/api/staff")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["username"], "@amit_coord")
        
        response = self.client.post("/api/staff", json={"username": "@amit_coord", "hospital": "Apollo", "role": "Coordinator"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        
        response = self.client.delete("/api/staff/@amit_coord")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        
        mock_schedule_res = MagicMock()
        mock_schedule_res.data = [{
            "schedule_id": 1,
            "patient_id": "P-100",
            "scheduled_date": "2026-06-10",
            "hospital": "Apollo",
            "blood_type": "O+",
            "status": "PENDING",
            "advance_days": 5
        }]
        
        def mock_table_schedule(name):
            t_mock = MagicMock()
            if name == "transfusion_schedule":
                t_mock.select.return_value.gte.return_value.lte.return_value.order.return_value.execute.return_value = mock_schedule_res
                t_mock.insert.return_value.execute.return_value = MagicMock(data=[])
            return t_mock
        mock_supabase.table.side_effect = mock_table_schedule
        
        response = self.client.get("/api/schedule?days=7")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["patient_id"], "P-100")
        
        response = self.client.post("/api/schedule", json={
            "patient_id": "P-100",
            "scheduled_date": "2026-06-10",
            "hospital": "Apollo",
            "blood_type": "O+"
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

    @patch('core.database.create_client')
    async def test_websocket_endpoint(self, mock_create_client):
        mock_supabase = MagicMock()
        mock_create_client.return_value = mock_supabase
        
        mock_emp_res = MagicMock()
        mock_emp_res.data = [{
            "request_id": "REQ-12345",
            "patient_id": "P-100",
            "blood_type": "O+",
            "city": "Hyderabad",
            "hospital_name": "Apollo",
            "status": "IN_PROGRESS",
            "created_at": "2026-06-04T12:00:00Z"
        }]
        
        mock_chain_res = MagicMock()
        mock_chain_res.data = [{
            "donor_id": "D-1",
            "donor_name": "Amit Sharma",
            "chain_position": 1,
            "status": "CONFIRMED",
            "antigen_score": 0.95
        }]
        
        def mock_table_ws(name):
            t_mock = MagicMock()
            if name == "emergency_requests":
                t_mock.select.return_value.eq.return_value.execute.return_value = mock_emp_res
            elif name == "blood_chains":
                t_mock.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_chain_res
            return t_mock
        mock_supabase.table.side_effect = mock_table_ws
        
        with self.client.websocket_connect("/ws/emergency") as websocket:
            data = websocket.receive_json()
            self.assertEqual(data["type"], "initial_state")
            self.assertEqual(len(data["data"]), 1)
            self.assertEqual(data["data"][0]["request_id"], "REQ-12345")
            self.assertEqual(len(data["data"][0]["chain"]), 1)
            self.assertEqual(data["data"][0]["chain"][0]["donor_id"], "D-1")

    @patch('services.alerts.httpx.AsyncClient')
    async def test_alerts_service(self, mock_http_client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_http_client.return_value.__aenter__.return_value = mock_client
        
        from services.alerts import send_alert, alert_critical_patient, alert_chain_break, alert_escalation, alert_success, alert_lora_received
        
        with patch('services.alerts.get_settings') as mock_settings:
            mock_s = MagicMock()
            mock_s.NTFY_TOPIC = "test-topic"
            mock_s.APP_BASE_URL = "http://localhost:8000"
            mock_settings.return_value = mock_s
            
            await alert_critical_patient("P-100", "O+", "Apollo")
            mock_client.post.assert_called_once()
            
            mock_client.post.reset_mock()
            await alert_chain_break("P-100", 2)
            mock_client.post.assert_called_once()
            
            mock_client.post.reset_mock()
            await alert_escalation("P-100", [{"name": "Bank A"}])
            mock_client.post.assert_called_once()
            
            mock_client.post.reset_mock()
            await alert_success("P-100", "Amit Sharma")
            mock_client.post.assert_called_once()
            
            mock_client.post.reset_mock()
            await alert_lora_received("GW-01", -85, "P-100")
            mock_client.post.assert_called_once()

if __name__ == '__main__':
    unittest.main()
