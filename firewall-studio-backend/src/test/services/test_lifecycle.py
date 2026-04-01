"""Tests for app.services.lifecycle — 100% coverage."""
import pytest
import json
from datetime import datetime, timedelta

from app.services.lifecycle import (
    get_valid_transitions,
    is_valid_transition,
    record_lifecycle_event,
    get_lifecycle_events,
    get_rule_timeline,
    transition_lifecycle,
    soft_delete_rule,
    restore_rule,
    check_expiring_rules,
    auto_expire_rules,
    bulk_certify,
    bulk_decommission,
    get_lifecycle_dashboard,
    NGDC_RULE_STATES,
    LEGACY_RULE_STATES,
    EVENT_TYPES,
    _load_lifecycle_events,
    _save_lifecycle_events,
)
import app.database as db


# ---- State Machine ----

class TestStateMachine:
    def test_ngdc_draft_to_submitted(self):
        assert "Submitted" in get_valid_transitions("Draft", is_legacy=False)

    def test_ngdc_submitted_to_in_progress(self):
        assert "In Progress" in get_valid_transitions("Submitted", is_legacy=False)

    def test_ngdc_submitted_to_rejected(self):
        assert "Rejected" in get_valid_transitions("Submitted", is_legacy=False)

    def test_ngdc_approved_to_deployed(self):
        assert "Deployed" in get_valid_transitions("Approved", is_legacy=False)

    def test_ngdc_deployed_to_certified(self):
        assert "Certified" in get_valid_transitions("Deployed", is_legacy=False)

    def test_ngdc_certified_to_expired(self):
        assert "Expired" in get_valid_transitions("Certified", is_legacy=False)

    def test_ngdc_decommissioned_terminal(self):
        assert get_valid_transitions("Decommissioned", is_legacy=False) == []

    def test_ngdc_deleted_terminal(self):
        assert get_valid_transitions("Deleted", is_legacy=False) == []

    def test_legacy_deployed_to_certified(self):
        assert "Certified" in get_valid_transitions("Deployed", is_legacy=True)

    def test_legacy_decommissioned_terminal(self):
        assert get_valid_transitions("Decommissioned", is_legacy=True) == []

    def test_unknown_state(self):
        assert get_valid_transitions("NonExistent", is_legacy=False) == []

    def test_is_valid_transition_true(self):
        assert is_valid_transition("Draft", "Submitted") is True

    def test_is_valid_transition_false(self):
        assert is_valid_transition("Draft", "Deployed") is False

    def test_is_valid_transition_legacy(self):
        assert is_valid_transition("Deployed", "Certified", is_legacy=True) is True

    def test_all_ngdc_states_covered(self):
        for state in NGDC_RULE_STATES:
            result = get_valid_transitions(state, is_legacy=False)
            assert isinstance(result, list)

    def test_all_legacy_states_covered(self):
        for state in LEGACY_RULE_STATES:
            result = get_valid_transitions(state, is_legacy=True)
            assert isinstance(result, list)

    def test_rejected_to_submitted(self):
        assert "Submitted" in get_valid_transitions("Rejected", is_legacy=False)

    def test_expired_to_certified(self):
        assert "Certified" in get_valid_transitions("Expired", is_legacy=False)

    def test_expired_to_decommissioning(self):
        assert "Decommissioning" in get_valid_transitions("Expired", is_legacy=False)


# ---- Lifecycle Events ----

class TestLifecycleEvents:
    @pytest.mark.asyncio
    async def test_record_event(self):
        event = await record_lifecycle_event(
            rule_id="R001", event_type="created",
            from_status=None, to_status="Draft",
            actor="test", module="test", details="unit test",
        )
        assert event["rule_id"] == "R001"
        assert event["event_type"] == "created"
        assert event["id"].startswith("evt-")

    @pytest.mark.asyncio
    async def test_get_events_all(self):
        await record_lifecycle_event(rule_id="R001", event_type="created")
        await record_lifecycle_event(rule_id="R002", event_type="submitted")
        events = await get_lifecycle_events()
        assert len(events) == 2

    @pytest.mark.asyncio
    async def test_get_events_by_rule_id(self):
        await record_lifecycle_event(rule_id="R001", event_type="created")
        await record_lifecycle_event(rule_id="R002", event_type="submitted")
        events = await get_lifecycle_events(rule_id="R001")
        assert len(events) == 1
        assert events[0]["rule_id"] == "R001"

    @pytest.mark.asyncio
    async def test_get_events_by_type(self):
        await record_lifecycle_event(rule_id="R001", event_type="created")
        await record_lifecycle_event(rule_id="R002", event_type="created")
        events = await get_lifecycle_events(event_type="created")
        assert len(events) == 2

    @pytest.mark.asyncio
    async def test_get_events_by_module(self):
        await record_lifecycle_event(rule_id="R001", event_type="created", module="studio")
        await record_lifecycle_event(rule_id="R002", event_type="created", module="migration")
        events = await get_lifecycle_events(module="studio")
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_get_events_pagination(self):
        for i in range(5):
            await record_lifecycle_event(rule_id=f"R{i:03d}", event_type="created")
        events = await get_lifecycle_events(limit=2, offset=1)
        assert len(events) == 2

    @pytest.mark.asyncio
    async def test_rule_timeline(self):
        await record_lifecycle_event(rule_id="R001", event_type="created")
        await record_lifecycle_event(rule_id="R001", event_type="submitted")
        await record_lifecycle_event(rule_id="R002", event_type="created")
        timeline = await get_rule_timeline("R001")
        assert len(timeline) == 2
        assert timeline[0]["event_type"] == "created"

    @pytest.mark.asyncio
    async def test_load_save_events(self):
        _save_lifecycle_events([{"id": "evt-test", "rule_id": "R001"}])
        loaded = _load_lifecycle_events()
        assert len(loaded) == 1
        assert loaded[0]["id"] == "evt-test"

    @pytest.mark.asyncio
    async def test_load_empty_events(self):
        loaded = _load_lifecycle_events()
        assert loaded == []


# ---- Lifecycle Transitions ----

class TestTransitionLifecycle:
    def _seed_rule(self, rule_id="R001", status="Draft", is_legacy=False):
        store = "legacy_rules" if is_legacy else "firewall_rules"
        id_field = "id" if is_legacy else "rule_id"
        rules = db._load(store) or []
        rule = {id_field: rule_id, "lifecycle_status": status, "rule_status": status,
                "status": status, "application": "TestApp"}
        rules.append(rule)
        db._save(store, rules)

    @pytest.mark.asyncio
    async def test_valid_transition(self):
        self._seed_rule("R001", "Draft")
        result = await transition_lifecycle("R001", "Submitted", actor="tester")
        assert result.get("lifecycle_status") == "Submitted"

    @pytest.mark.asyncio
    async def test_invalid_transition(self):
        self._seed_rule("R001", "Draft")
        result = await transition_lifecycle("R001", "Deployed")
        assert "error" in result
        assert "Invalid transition" in result["error"]

    @pytest.mark.asyncio
    async def test_rule_not_found(self):
        result = await transition_lifecycle("NONEXIST", "Submitted")
        assert "error" in result
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_deployed_transition(self):
        self._seed_rule("R001", "Approved")
        result = await transition_lifecycle("R001", "Deployed")
        assert result.get("status") == "Deployed"
        assert "deployed_at" in result

    @pytest.mark.asyncio
    async def test_certified_transition(self):
        self._seed_rule("R001", "Deployed")
        # Need org_config for expiry_days
        db._save("org_config", {"auto_certify_days": 365})
        result = await transition_lifecycle("R001", "Certified")
        assert result.get("status") == "Certified"
        assert "expiry_date" in result

    @pytest.mark.asyncio
    async def test_expired_transition(self):
        self._seed_rule("R001", "Certified")
        result = await transition_lifecycle("R001", "Expired")
        assert result.get("status") == "Expired"

    @pytest.mark.asyncio
    async def test_decommissioning_transition(self):
        self._seed_rule("R001", "Deployed")
        result = await transition_lifecycle("R001", "Decommissioning")
        assert result.get("status") == "Decommissioning"
        assert "decommission_requested_at" in result

    @pytest.mark.asyncio
    async def test_decommissioned_transition(self):
        self._seed_rule("R001", "Decommissioning")
        result = await transition_lifecycle("R001", "Decommissioned")
        assert result.get("status") == "Decommissioned"

    @pytest.mark.asyncio
    async def test_rejected_transition(self):
        self._seed_rule("R001", "Submitted")
        result = await transition_lifecycle("R001", "Rejected")
        assert result.get("status") == "Rejected"

    @pytest.mark.asyncio
    async def test_approved_transition(self):
        self._seed_rule("R001", "In Progress")
        result = await transition_lifecycle("R001", "Approved")
        assert result.get("status") == "Approved"

    @pytest.mark.asyncio
    async def test_in_progress_transition(self):
        self._seed_rule("R001", "Submitted")
        result = await transition_lifecycle("R001", "In Progress")
        assert result.get("status") == "Pending Review"

    @pytest.mark.asyncio
    async def test_submitted_transition(self):
        self._seed_rule("R001", "Rejected")
        result = await transition_lifecycle("R001", "Submitted")
        assert result.get("status") == "Pending Review"

    @pytest.mark.asyncio
    async def test_legacy_transition(self):
        self._seed_rule("R001", "Deployed", is_legacy=True)
        result = await transition_lifecycle("R001", "Certified", is_legacy=True)
        assert result.get("lifecycle_status") == "Certified"

    @pytest.mark.asyncio
    async def test_records_history(self):
        self._seed_rule("R001", "Draft")
        await transition_lifecycle("R001", "Submitted")
        history = db._load("rule_history") or []
        assert any("R001" in str(h) for h in history)


# ---- Soft Delete & Restore ----

class TestSoftDeleteRestore:
    def _seed_rule(self, rule_id="R001", status="Deployed", is_legacy=False):
        store = "legacy_rules" if is_legacy else "firewall_rules"
        id_field = "id" if is_legacy else "rule_id"
        rules = db._load(store) or []
        rules.append({id_field: rule_id, "lifecycle_status": status, "rule_status": status, "status": status})
        db._save(store, rules)

    @pytest.mark.asyncio
    async def test_soft_delete(self):
        self._seed_rule("R001")
        result = await soft_delete_rule("R001", actor="admin", reason="cleanup")
        assert result.get("lifecycle_status") == "Deleted"
        assert result.get("delete_reason") == "cleanup"

    @pytest.mark.asyncio
    async def test_soft_delete_not_found(self):
        result = await soft_delete_rule("NONEXIST")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_restore(self):
        self._seed_rule("R001", "Deployed")
        await soft_delete_rule("R001")
        result = await restore_rule("R001")
        assert result.get("lifecycle_status") == "Deployed"
        assert "deleted_at" not in result

    @pytest.mark.asyncio
    async def test_restore_not_deleted(self):
        self._seed_rule("R001", "Deployed")
        result = await restore_rule("R001")
        assert "error" in result
        assert "not in Deleted state" in result["error"]

    @pytest.mark.asyncio
    async def test_restore_not_found(self):
        result = await restore_rule("NONEXIST")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_soft_delete_legacy(self):
        self._seed_rule("L001", "Deployed", is_legacy=True)
        result = await soft_delete_rule("L001", is_legacy=True)
        assert result.get("lifecycle_status") == "Deleted"

    @pytest.mark.asyncio
    async def test_restore_legacy(self):
        self._seed_rule("L001", "Deployed", is_legacy=True)
        await soft_delete_rule("L001", is_legacy=True)
        result = await restore_rule("L001", is_legacy=True)
        assert result.get("lifecycle_status") == "Deployed"


# ---- Certification & Expiry ----

class TestCertificationExpiry:
    def _seed_rule_with_expiry(self, rule_id, expiry, status="Certified"):
        rules = db._load("firewall_rules") or []
        rules.append({"rule_id": rule_id, "lifecycle_status": status, "expiry_date": expiry, "application": "TestApp"})
        db._save("firewall_rules", rules)

    @pytest.mark.asyncio
    async def test_check_expiring(self):
        future = (datetime.utcnow() + timedelta(days=10)).isoformat()
        self._seed_rule_with_expiry("R001", future)
        result = await check_expiring_rules(days_ahead=30)
        assert result["expiring_count"] >= 1

    @pytest.mark.asyncio
    async def test_check_expired(self):
        past = (datetime.utcnow() - timedelta(days=10)).isoformat()
        self._seed_rule_with_expiry("R001", past)
        result = await check_expiring_rules()
        assert result["expired_count"] >= 1

    @pytest.mark.asyncio
    async def test_check_no_expiry(self):
        rules = db._load("firewall_rules") or []
        rules.append({"rule_id": "R001", "lifecycle_status": "Draft"})
        db._save("firewall_rules", rules)
        result = await check_expiring_rules()
        assert result["expiring_count"] == 0

    @pytest.mark.asyncio
    async def test_check_skips_deleted(self):
        past = (datetime.utcnow() - timedelta(days=10)).isoformat()
        self._seed_rule_with_expiry("R001", past, status="Deleted")
        result = await check_expiring_rules()
        assert result["expired_count"] == 0

    @pytest.mark.asyncio
    async def test_check_invalid_date(self):
        self._seed_rule_with_expiry("R001", "not-a-date")
        result = await check_expiring_rules()
        assert result["expiring_count"] == 0

    @pytest.mark.asyncio
    async def test_auto_expire(self):
        past = (datetime.utcnow() - timedelta(days=10)).isoformat()
        self._seed_rule_with_expiry("R001", past)
        result = await auto_expire_rules()
        assert result["count"] >= 1
        assert "R001" in result["transitioned"]

    @pytest.mark.asyncio
    async def test_auto_expire_skips_non_certified(self):
        past = (datetime.utcnow() - timedelta(days=10)).isoformat()
        self._seed_rule_with_expiry("R001", past, status="Deployed")
        result = await auto_expire_rules()
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_auto_expire_legacy(self):
        past = (datetime.utcnow() - timedelta(days=10)).isoformat()
        rules = db._load("legacy_rules") or []
        rules.append({"id": "L001", "lifecycle_status": "Certified", "expiry_date": past})
        db._save("legacy_rules", rules)
        result = await auto_expire_rules()
        assert "L001" in result["transitioned"]


# ---- Bulk Operations ----

class TestBulkOperations:
    def _seed_rules(self):
        rules = [
            {"rule_id": "R001", "lifecycle_status": "Deployed", "rule_status": "Deployed", "status": "Deployed"},
            {"rule_id": "R002", "lifecycle_status": "Deployed", "rule_status": "Deployed", "status": "Deployed"},
        ]
        db._save("firewall_rules", rules)

    @pytest.mark.asyncio
    async def test_bulk_certify(self):
        self._seed_rules()
        db._save("org_config", {"auto_certify_days": 365})
        result = await bulk_certify(["R001", "R002"])
        assert result["total"] == 2
        assert result["succeeded"] >= 1

    @pytest.mark.asyncio
    async def test_bulk_certify_not_found(self):
        result = await bulk_certify(["NONEXIST"])
        assert result["failed"] >= 1

    @pytest.mark.asyncio
    async def test_bulk_decommission(self):
        self._seed_rules()
        result = await bulk_decommission(["R001", "R002"], reason="EOL")
        assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_bulk_decommission_not_found(self):
        result = await bulk_decommission(["NONEXIST"])
        assert result["failed"] >= 1


# ---- Dashboard ----

class TestDashboard:
    @pytest.mark.asyncio
    async def test_empty_dashboard(self):
        result = await get_lifecycle_dashboard()
        assert "ngdc_rules" in result
        assert "legacy_rules" in result
        assert "certification" in result
        assert "decommission_queue" in result
        assert "recent_events" in result

    @pytest.mark.asyncio
    async def test_dashboard_with_rules(self):
        db._save("firewall_rules", [
            {"rule_id": "R001", "lifecycle_status": "Deployed", "application": "CRM"},
            {"rule_id": "R002", "lifecycle_status": "Certified", "application": "CRM",
             "expiry_date": (datetime.utcnow() + timedelta(days=10)).isoformat()},
        ])
        db._save("legacy_rules", [
            {"id": "L001", "lifecycle_status": "Deployed", "app_name": "PAY"},
        ])
        result = await get_lifecycle_dashboard()
        assert result["ngdc_rules"]["total"] == 2
        assert result["legacy_rules"]["total"] == 1


# ---- Event Types Constant ----

class TestEventTypes:
    def test_event_types_list(self):
        assert "created" in EVENT_TYPES
        assert "submitted" in EVENT_TYPES
        assert "approved" in EVENT_TYPES
        assert "rejected" in EVENT_TYPES
        assert "deployed" in EVENT_TYPES
        assert "soft_deleted" in EVENT_TYPES
        assert "restored" in EVENT_TYPES
