"""Tests for app.database partial migration functions — 100% coverage."""
import pytest
import app.database as db


class TestPartialMigrationStatuses:
    def test_statuses_list(self):
        assert "Not Started" in db.PARTIAL_MIGRATION_STATUSES
        assert "In Progress" in db.PARTIAL_MIGRATION_STATUSES
        assert "Partially Migrated" in db.PARTIAL_MIGRATION_STATUSES
        assert "Completed" in db.PARTIAL_MIGRATION_STATUSES
        assert "Heritage Dependency" in db.PARTIAL_MIGRATION_STATUSES
        assert "Rollback" in db.PARTIAL_MIGRATION_STATUSES

    def test_transitions_not_started(self):
        assert db.PARTIAL_MIGRATION_TRANSITIONS["Not Started"] == ["In Progress"]

    def test_transitions_completed_terminal(self):
        assert db.PARTIAL_MIGRATION_TRANSITIONS["Completed"] == []


class TestGenerateLegacyGroupName:
    def test_basic(self):
        name = db.generate_legacy_group_name("CRM", "DC_LEGACY_A", "WEB")
        assert name == "leg-CRM-LGA-WEB"

    def test_with_suffix(self):
        name = db.generate_legacy_group_name("CRM", "DC_LEGACY_B", "APP", suffix="01")
        assert name == "leg-CRM-LGB-APP-01"

    def test_no_dc(self):
        name = db.generate_legacy_group_name("CRM", "", "DB")
        assert name == "leg-CRM-DB"

    def test_no_component(self):
        name = db.generate_legacy_group_name("CRM", "DC_LEGACY_A", "")
        assert name == "leg-CRM-LGA"

    def test_lowercase_input(self):
        name = db.generate_legacy_group_name("crm", "DC_LEGACY_A", "web")
        assert name == "leg-CRM-LGA-WEB"


class TestAppMigrationSummary:
    def _seed_app_dc_mappings(self, mappings):
        db._save("app_dc_mappings", mappings)

    @pytest.mark.asyncio
    async def test_empty(self):
        result = await db.get_app_migration_summary()
        assert result == []

    @pytest.mark.asyncio
    async def test_full_ngdc(self):
        self._seed_app_dc_mappings([
            {"app_id": "CRM", "component": "WEB", "dc_location": "NGDC", "dc": "NGDC1", "nh": "NH01", "sz": "GEN"},
            {"app_id": "CRM", "component": "APP", "dc_location": "NGDC", "dc": "NGDC1", "nh": "NH01", "sz": "GEN"},
        ])
        result = await db.get_app_migration_summary()
        assert len(result) == 1
        assert result[0]["migration_scenario"] == "Full NGDC"
        assert result[0]["pct_migrated"] == 100

    @pytest.mark.asyncio
    async def test_full_legacy(self):
        self._seed_app_dc_mappings([
            {"app_id": "PAY", "component": "WEB", "dc_location": "Legacy", "legacy_dc": "DC_LEGACY_A"},
            {"app_id": "PAY", "component": "DB", "dc_location": "Legacy", "legacy_dc": "DC_LEGACY_A"},
        ])
        result = await db.get_app_migration_summary()
        assert result[0]["migration_scenario"] == "Full Legacy"
        assert result[0]["pct_migrated"] == 0

    @pytest.mark.asyncio
    async def test_partial(self):
        self._seed_app_dc_mappings([
            {"app_id": "CRM", "component": "WEB", "dc_location": "NGDC", "dc": "NGDC1", "nh": "NH01", "sz": "GEN"},
            {"app_id": "CRM", "component": "DB", "dc_location": "Legacy", "legacy_dc": "DC_LEGACY_A"},
        ])
        result = await db.get_app_migration_summary()
        assert result[0]["migration_scenario"] == "Partial"
        assert result[0]["pct_migrated"] == 50

    @pytest.mark.asyncio
    async def test_multiple_apps(self):
        self._seed_app_dc_mappings([
            {"app_id": "CRM", "component": "WEB", "dc_location": "NGDC"},
            {"app_id": "PAY", "component": "WEB", "dc_location": "Legacy"},
        ])
        result = await db.get_app_migration_summary()
        assert len(result) == 2


class TestAppMigrationStatus:
    @pytest.mark.asyncio
    async def test_found(self):
        db._save("app_dc_mappings", [
            {"app_id": "CRM", "component": "WEB", "dc_location": "NGDC"},
        ])
        result = await db.get_app_migration_status("CRM")
        assert result is not None
        assert result["app_id"] == "CRM"

    @pytest.mark.asyncio
    async def test_not_found(self):
        result = await db.get_app_migration_status("NONEXIST")
        assert result is None


class TestClassifyRuleEndpoints:
    def _seed_mappings(self, mappings):
        db._save("app_dc_mappings", mappings)

    @pytest.mark.asyncio
    async def test_ngdc_to_ngdc(self):
        self._seed_mappings([
            {"app_id": "CRM", "component": "WEB", "dc_location": "NGDC"},
            {"app_id": "CRM", "component": "APP", "dc_location": "NGDC"},
        ])
        result = await db.classify_rule_endpoints({
            "source_app": "CRM", "source_component": "WEB",
            "destination_app": "CRM", "destination_component": "APP",
        })
        assert result["scenario"] == "NGDC-to-NGDC"

    @pytest.mark.asyncio
    async def test_legacy_to_legacy(self):
        self._seed_mappings([
            {"app_id": "PAY", "component": "WEB", "dc_location": "Legacy"},
            {"app_id": "PAY", "component": "DB", "dc_location": "Legacy"},
        ])
        result = await db.classify_rule_endpoints({
            "source_app": "PAY", "source_component": "WEB",
            "destination_app": "PAY", "destination_component": "DB",
        })
        assert result["scenario"] == "Legacy-to-Legacy"

    @pytest.mark.asyncio
    async def test_ngdc_to_legacy(self):
        self._seed_mappings([
            {"app_id": "CRM", "component": "WEB", "dc_location": "NGDC"},
            {"app_id": "PAY", "component": "DB", "dc_location": "Legacy"},
        ])
        result = await db.classify_rule_endpoints({
            "source_app": "CRM", "source_component": "WEB",
            "destination_app": "PAY", "destination_component": "DB",
        })
        assert result["scenario"] == "NGDC-to-Legacy"
        assert result["heritage_direction"] == "NGDC-to-Heritage"

    @pytest.mark.asyncio
    async def test_legacy_to_ngdc(self):
        self._seed_mappings([
            {"app_id": "PAY", "component": "WEB", "dc_location": "Legacy"},
            {"app_id": "CRM", "component": "APP", "dc_location": "NGDC"},
        ])
        result = await db.classify_rule_endpoints({
            "source_app": "PAY", "source_component": "WEB",
            "destination_app": "CRM", "destination_component": "APP",
        })
        assert result["scenario"] == "Legacy-to-NGDC"

    @pytest.mark.asyncio
    async def test_unknown(self):
        result = await db.classify_rule_endpoints({
            "source_app": "UNKNOWN", "destination_app": "UNKNOWN2",
        })
        assert result["scenario"] == "Unknown"

    @pytest.mark.asyncio
    async def test_app_majority_fallback(self):
        self._seed_mappings([
            {"app_id": "CRM", "component": "WEB", "dc_location": "NGDC"},
            {"app_id": "CRM", "component": "APP", "dc_location": "NGDC"},
            {"app_id": "CRM", "component": "DB", "dc_location": "Legacy"},
        ])
        result = await db.classify_rule_endpoints({
            "source_app": "CRM", "destination_app": "CRM",
        })
        # Majority is NGDC
        assert result["source_dc_location"] == "NGDC"


class TestDetermineCrossDCBoundaries:
    @pytest.mark.asyncio
    async def test_ngdc_to_ngdc(self):
        db._save("app_dc_mappings", [
            {"app_id": "CRM", "component": "WEB", "dc_location": "NGDC"},
        ])
        result = await db.determine_cross_dc_boundaries({
            "source_app": "CRM", "source_component": "WEB",
            "destination_app": "CRM", "destination_component": "WEB",
        })
        assert "boundaries" in result or "scenario" in str(result)

    @pytest.mark.asyncio
    async def test_cross_dc(self):
        db._save("app_dc_mappings", [
            {"app_id": "CRM", "component": "WEB", "dc_location": "NGDC", "nh": "NH01", "sz": "GEN"},
            {"app_id": "PAY", "component": "DB", "dc_location": "Legacy"},
        ])
        db._save_ref("firewall_devices", [{"id": "FW001", "nh": "NH01", "sz": "GEN", "device_name": "fw-gen-01"}])
        result = await db.determine_cross_dc_boundaries({
            "source_app": "CRM", "source_component": "WEB",
            "destination_app": "PAY", "destination_component": "DB",
            "source_zone": "GEN", "source_nh": "NH01",
        })
        assert result is not None


class TestValidateBirthrightCrossDC:
    @pytest.mark.asyncio
    async def test_ngdc_to_ngdc_delegates(self):
        db._save("app_dc_mappings", [
            {"app_id": "CRM", "component": "WEB", "dc_location": "NGDC"},
        ])
        db._save_ref("policy_matrix", [])
        result = await db.validate_birthright_cross_dc({
            "source_app": "CRM", "source_component": "WEB",
            "destination_app": "CRM", "destination_component": "WEB",
            "environment": "Production",
        })
        assert "compliant" in result

    @pytest.mark.asyncio
    async def test_legacy_to_legacy(self):
        db._save("app_dc_mappings", [
            {"app_id": "PAY", "component": "WEB", "dc_location": "Legacy"},
            {"app_id": "PAY", "component": "DB", "dc_location": "Legacy"},
        ])
        result = await db.validate_birthright_cross_dc({
            "source_app": "PAY", "source_component": "WEB",
            "destination_app": "PAY", "destination_component": "DB",
        })
        assert result["compliant"] is True
        assert result["matrix_used"] == "Heritage DC"

    @pytest.mark.asyncio
    async def test_cross_dc_with_heritage_matrix(self):
        db._save("app_dc_mappings", [
            {"app_id": "CRM", "component": "WEB", "dc_location": "NGDC"},
            {"app_id": "PAY", "component": "DB", "dc_location": "Legacy"},
        ])
        db._save("heritage_dc_matrix", [
            {"direction": "NGDC-to-Heritage", "new_dc_zone": "GEN", "action": "Permitted", "reason": "Default"},
        ])
        result = await db.validate_birthright_cross_dc({
            "source_app": "CRM", "source_component": "WEB",
            "destination_app": "PAY", "destination_component": "DB",
            "source_zone": "GEN",
        })
        assert result["matrix_used"] == "Heritage DC"

    @pytest.mark.asyncio
    async def test_cross_dc_no_match(self):
        db._save("app_dc_mappings", [
            {"app_id": "CRM", "component": "WEB", "dc_location": "NGDC"},
            {"app_id": "PAY", "component": "DB", "dc_location": "Legacy"},
        ])
        db._save("heritage_dc_matrix", [])
        result = await db.validate_birthright_cross_dc({
            "source_app": "CRM", "source_component": "WEB",
            "destination_app": "PAY", "destination_component": "DB",
            "source_zone": "CDE",
        })
        assert len(result["warnings"]) > 0

    @pytest.mark.asyncio
    async def test_cross_dc_blocked(self):
        db._save("app_dc_mappings", [
            {"app_id": "CRM", "component": "WEB", "dc_location": "NGDC"},
            {"app_id": "PAY", "component": "DB", "dc_location": "Legacy"},
        ])
        db._save("heritage_dc_matrix", [
            {"direction": "NGDC-to-Heritage", "new_dc_zone": "CDE", "action": "Blocked", "reason": "Security"},
        ])
        result = await db.validate_birthright_cross_dc({
            "source_app": "CRM", "source_component": "WEB",
            "destination_app": "PAY", "destination_component": "DB",
            "source_zone": "CDE",
        })
        assert result["compliant"] is False

    @pytest.mark.asyncio
    async def test_cross_dc_exception(self):
        db._save("app_dc_mappings", [
            {"app_id": "CRM", "component": "WEB", "dc_location": "NGDC"},
            {"app_id": "PAY", "component": "DB", "dc_location": "Legacy"},
        ])
        db._save("heritage_dc_matrix", [
            {"direction": "NGDC-to-Heritage", "new_dc_zone": "GEN", "action": "Exception Required", "reason": "Needs review"},
        ])
        result = await db.validate_birthright_cross_dc({
            "source_app": "CRM", "source_component": "WEB",
            "destination_app": "PAY", "destination_component": "DB",
            "source_zone": "GEN",
        })
        assert len(result["warnings"]) > 0


class TestCompileHybridRule:
    @pytest.mark.asyncio
    async def test_rule_not_found(self):
        result = await db.compile_hybrid_rule("NONEXIST")
        assert result is None

    @pytest.mark.asyncio
    async def test_ngdc_to_ngdc_delegates(self):
        db._save("firewall_rules", [{"rule_id": "R001", "application": "CRM",
                                      "source_app": "CRM", "source_component": "WEB",
                                      "destination_app": "CRM", "destination_component": "APP"}])
        db._save("app_dc_mappings", [
            {"app_id": "CRM", "component": "WEB", "dc_location": "NGDC"},
            {"app_id": "CRM", "component": "APP", "dc_location": "NGDC"},
        ])
        result = await db.compile_hybrid_rule("R001")
        # Will delegate to compile_egress_ingress
        assert result is not None

    @pytest.mark.asyncio
    async def test_cross_dc_compilation(self):
        db._save("firewall_rules", [{
            "rule_id": "R002", "application": "CRM",
            "source_app": "CRM", "source_component": "WEB",
            "destination_app": "PAY", "destination_component": "DB",
            "source": "10.0.0.1", "destination": "10.0.0.2",
            "action": "permit", "protocol": "tcp", "port": "443",
            "name": "crm-to-pay",
        }])
        db._save("app_dc_mappings", [
            {"app_id": "CRM", "component": "WEB", "dc_location": "NGDC", "nh": "NH01", "sz": "GEN"},
            {"app_id": "PAY", "component": "DB", "dc_location": "Legacy"},
        ])
        result = await db.compile_hybrid_rule("R002")
        assert result["scenario"] == "NGDC-to-Legacy"
        assert len(result["compiled_rules"]) == 3  # NGDC + Legacy + DCI

    @pytest.mark.asyncio
    async def test_legacy_rule_lookup(self):
        db._save("legacy_rules", [{
            "id": "L001", "source_app": "PAY", "destination_app": "CRM",
            "source_component": "WEB", "destination_component": "APP",
            "source": "10.0.0.1", "destination": "10.0.0.2",
        }])
        db._save("app_dc_mappings", [
            {"app_id": "PAY", "component": "WEB", "dc_location": "Legacy"},
            {"app_id": "CRM", "component": "APP", "dc_location": "NGDC"},
        ])
        result = await db.compile_hybrid_rule("L001")
        assert result is not None


class TestAppLifecycleStatus:
    @pytest.mark.asyncio
    async def test_not_found(self):
        result = await db.get_app_lifecycle_status("NONEXIST")
        assert result["status"] == "Unknown"

    @pytest.mark.asyncio
    async def test_full_ngdc_completed(self):
        db._save("app_dc_mappings", [
            {"app_id": "CRM", "component": "WEB", "dc_location": "NGDC"},
        ])
        result = await db.get_app_lifecycle_status("CRM")
        assert result["status"] == "Completed"

    @pytest.mark.asyncio
    async def test_full_legacy_not_started(self):
        db._save("app_dc_mappings", [
            {"app_id": "PAY", "component": "WEB", "dc_location": "Legacy"},
        ])
        result = await db.get_app_lifecycle_status("PAY")
        assert result["status"] == "Not Started"

    @pytest.mark.asyncio
    async def test_partial_migrated(self):
        db._save("app_dc_mappings", [
            {"app_id": "CRM", "component": "WEB", "dc_location": "NGDC"},
            {"app_id": "CRM", "component": "DB", "dc_location": "Legacy"},
        ])
        result = await db.get_app_lifecycle_status("CRM")
        assert result["status"] == "Partially Migrated"


class TestGenerateHybridGroupNames:
    @pytest.mark.asyncio
    async def test_not_found(self):
        result = await db.generate_hybrid_group_names("NONEXIST")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_mixed_groups(self):
        db._save("app_dc_mappings", [
            {"app_id": "CRM", "component": "WEB", "dc_location": "NGDC", "nh": "NH01", "sz": "GEN", "dc": "NGDC1"},
            {"app_id": "CRM", "component": "DB", "dc_location": "Legacy", "legacy_dc": "DC_LEGACY_A"},
        ])
        result = await db.generate_hybrid_group_names("CRM")
        assert len(result["groups"]) == 2
        ngdc_group = next(g for g in result["groups"] if g["dc_location"] == "NGDC")
        legacy_group = next(g for g in result["groups"] if g["dc_location"] == "Legacy")
        assert "grp-" in ngdc_group["group_name"] or "CRM" in ngdc_group["group_name"]
        assert legacy_group["group_name"].startswith("leg-")
