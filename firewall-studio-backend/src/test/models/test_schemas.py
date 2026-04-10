"""Tests for app.models.schemas — 100% coverage."""
import pytest
from app.models.schemas import (
    RuleStatus, PolicyResult, MigrationStatus, MappingStatus, SourceType,
    SourceConfig, DestinationConfig, FirewallRule, FirewallRuleCreate, FirewallRuleUpdate,
    MigrationDetails, MigrationMapping, MigrationRuleLifecycle, MigrationCreate,
    Neighbourhood, NGDCDataCenter, SecurityZone, PredefinedDestination,
    PolicyValidationRequest, PolicyValidationResult,
    CHGRequest, RuleHistoryEntry,
)


class TestEnums:
    def test_rule_status_values(self):
        assert RuleStatus.DRAFT == "Draft"
        assert RuleStatus.DEPLOYED == "Deployed"
        assert RuleStatus.PENDING_REVIEW == "Pending Review"
        assert RuleStatus.CERTIFIED == "Certified"
        assert RuleStatus.EXPIRED == "Expired"
        assert RuleStatus.DELETED == "Deleted"

    def test_policy_result_values(self):
        assert PolicyResult.PERMITTED == "Permitted"
        assert PolicyResult.BLOCKED == "Blocked"
        assert PolicyResult.EXCEPTION_REQUIRED == "Exception Required"
        assert PolicyResult.NEEDS_REVIEW == "Needs Review"

    def test_migration_status_values(self):
        assert MigrationStatus.AUTO_MAPPED == "Auto-Mapped"
        assert MigrationStatus.NEEDS_REVIEW == "Needs Review"
        assert MigrationStatus.NEW_GROUP == "New Group"
        assert MigrationStatus.CONFLICT == "Conflict"
        assert MigrationStatus.BLOCKED == "Blocked"
        assert MigrationStatus.DRAFT == "Draft"
        assert MigrationStatus.POLICY_REVIEW == "Policy Review"

    def test_mapping_status_values(self):
        assert MappingStatus.AUTOMAPPED == "Automapped"
        assert MappingStatus.NEEDS_REVIEW == "Needs Review"
        assert MappingStatus.BLOCKED == "Blocked"

    def test_source_type_values(self):
        assert SourceType.SINGLE_IP == "Single IP"
        assert SourceType.SUBNET == "Subnet"
        assert SourceType.GROUP == "Group"


class TestSourceConfig:
    def test_defaults(self):
        sc = SourceConfig()
        assert sc.source_type == SourceType.SINGLE_IP
        assert sc.ports == "TCP 8080"
        assert sc.ip_address is None
        assert sc.cidr is None
        assert sc.group_name is None
        assert sc.neighbourhood is None
        assert sc.security_zone is None

    def test_custom_values(self):
        sc = SourceConfig(
            source_type=SourceType.GROUP,
            group_name="grp-CRM-NH02-GEN-APP",
            ports="TCP 443",
            neighbourhood="NH02",
            security_zone="GEN",
        )
        assert sc.source_type == SourceType.GROUP
        assert sc.group_name == "grp-CRM-NH02-GEN-APP"


class TestDestinationConfig:
    def test_defaults(self):
        dc = DestinationConfig(name="TestDest")
        assert dc.name == "TestDest"
        assert dc.ports == "TCP 8443"
        assert dc.is_predefined is True
        assert dc.security_zone is None
        assert dc.dest_ip is None

    def test_custom_values(self):
        dc = DestinationConfig(name="Custom", security_zone="CDE", dest_ip="10.0.0.1", ports="TCP 80", is_predefined=False)
        assert dc.dest_ip == "10.0.0.1"
        assert dc.is_predefined is False


class TestFirewallRule:
    def test_defaults(self):
        rule = FirewallRule(
            rule_id="R001",
            source=SourceConfig(),
            destination=DestinationConfig(name="Dest"),
        )
        assert rule.rule_id == "R001"
        assert rule.application == "Ordering System"
        assert rule.environment == "Production"
        assert rule.datacenter == "DC1"
        assert rule.policy_result == PolicyResult.PERMITTED
        assert rule.status == RuleStatus.DRAFT
        assert rule.owner == "Jane Smith"

    def test_custom_rule(self):
        rule = FirewallRule(
            rule_id="R002",
            application="CRM",
            environment="Staging",
            datacenter="DC2",
            source=SourceConfig(source_type=SourceType.GROUP, group_name="grp-test"),
            destination=DestinationConfig(name="Target"),
            status=RuleStatus.DEPLOYED,
            owner="John",
            id="custom-id",
            expiry="2025-12-31",
        )
        assert rule.id == "custom-id"
        assert rule.expiry == "2025-12-31"


class TestFirewallRuleCreate:
    def test_defaults(self):
        rc = FirewallRuleCreate(
            source=SourceConfig(),
            destination=DestinationConfig(name="Dest"),
        )
        assert rc.application == "Ordering System"
        assert rc.owner == "Jane Smith"


class TestFirewallRuleUpdate:
    def test_all_none(self):
        ru = FirewallRuleUpdate()
        assert ru.source is None
        assert ru.destination is None
        assert ru.status is None
        assert ru.owner is None
        assert ru.expiry is None

    def test_partial_update(self):
        ru = FirewallRuleUpdate(status=RuleStatus.DEPLOYED, owner="Admin")
        assert ru.status == RuleStatus.DEPLOYED
        assert ru.owner == "Admin"


class TestMigrationModels:
    def test_migration_details(self):
        md = MigrationDetails(application="CRM", source_legacy_dc="DC1", target_ngdc="NGDC1")
        assert md.status == "Draft"
        assert md.map_to_standard_groups is True
        assert md.map_to_subnet_cidr is False

    def test_migration_mapping(self):
        mm = MigrationMapping(migration_id="M001", legacy_source="src", ngdc_target="tgt")
        assert mm.mapping_status == MigrationStatus.AUTO_MAPPED
        assert mm.trust_zones_automapped == 0
        assert mm.related_policies == []

    def test_migration_rule_lifecycle(self):
        mrl = MigrationRuleLifecycle(migration_id="M001", rule_id="R001", source="src", ngdc_target="tgt")
        assert mrl.mapping_status == "Draft"

    def test_migration_create(self):
        mc = MigrationCreate(application="CRM", source_legacy_dc="DC1", target_ngdc="NGDC1")
        assert mc.map_to_standard_groups is True


class TestReferenceModels:
    def test_neighbourhood(self):
        n = Neighbourhood(name="NH01")
        assert n.subnets == []

    def test_ngdc_datacenter(self):
        dc = NGDCDataCenter(name="NGDC1", code="N1")
        assert dc.neighbourhoods == []
        assert dc.ip_groups == []
        assert dc.rule_count == 0

    def test_security_zone(self):
        sz = SecurityZone(name="General", code="GEN")
        assert sz.description == ""

    def test_predefined_destination(self):
        pd = PredefinedDestination(name="Internet", security_zone="DMZ")
        assert pd.description is None


class TestPolicyValidation:
    def test_request(self):
        req = PolicyValidationRequest(
            source=SourceConfig(),
            destination=DestinationConfig(name="Dest"),
        )
        assert req.application == ""
        assert req.environment == "Production"

    def test_result(self):
        res = PolicyValidationResult(result=PolicyResult.PERMITTED, message="OK")
        assert res.details == []
        assert res.ngdc_zone_check is True
        assert res.birthright_compliant is True


class TestCHGRequest:
    def test_defaults(self):
        chg = CHGRequest(chg_number="CHG001")
        assert chg.status == "Open"
        assert chg.rule_ids == []
        assert chg.description == ""


class TestRuleHistoryEntry:
    def test_fields(self):
        entry = RuleHistoryEntry(rule_id="R001", action="Created", timestamp="2024-01-01T00:00:00", user="admin")
        assert entry.details == ""
        assert entry.id is None
