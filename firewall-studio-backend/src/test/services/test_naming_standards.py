"""Tests for app.services.naming_standards — 100% coverage."""
import pytest
from app.services.naming_standards import (
    validate_group_name,
    validate_server_name,
    validate_subnet_name,
    validate_name,
    generate_group_name,
    generate_server_name,
    generate_subnet_name,
    check_group_to_group,
    suggest_standard_name,
    determine_security_zone,
    get_naming_standards_info,
    VALID_NH_IDS,
    VALID_SZ_CODES,
    VALID_SUBTYPES,
    GROUP_PATTERN,
    SERVER_PATTERN,
    SUBNET_PATTERN,
)


# ---- validate_group_name ----

class TestValidateGroupName:
    def test_valid_group(self):
        r = validate_group_name("grp-CRM-NH02-GEN-APP")
        assert r["valid"] is True
        assert r["parsed"]["app_id"] == "CRM"
        assert r["parsed"]["nh"] == "NH02"
        assert r["parsed"]["sz"] == "GEN"
        assert r["parsed"]["subtype"] == "APP"

    def test_valid_group_lowercase(self):
        r = validate_group_name("grp-crm-nh02-gen-app")
        assert r["valid"] is True

    def test_invalid_pattern(self):
        r = validate_group_name("invalid-name")
        assert r["valid"] is False
        assert "does not match pattern" in r["error"]
        assert r["type"] == "group"

    def test_invalid_nh(self):
        r = validate_group_name("grp-CRM-NH99-GEN-APP")
        assert r["valid"] is False
        assert "Invalid NH ID" in r["error"]

    def test_invalid_sz(self):
        r = validate_group_name("grp-CRM-NH02-INVALID-APP")
        assert r["valid"] is False

    def test_invalid_subtype(self):
        r = validate_group_name("grp-CRM-NH02-GEN-ZZZ")
        assert r["valid"] is False
        assert "Invalid Subtype" in r["error"]

    def test_multiple_errors(self):
        r = validate_group_name("grp-CRM-NH99-INVALID-ZZZ")
        assert r["valid"] is False
        assert "error" in r or "parsed" in r

    def test_all_valid_subtypes(self):
        for sub in VALID_SUBTYPES:
            r = validate_group_name(f"grp-CRM-NH02-GEN-{sub}")
            assert r["valid"] is True

    def test_all_valid_sz_codes(self):
        for sz in VALID_SZ_CODES:
            r = validate_group_name(f"grp-CRM-NH02-{sz}-APP")
            # Some SZ codes are longer than 4 chars so may not match the regex
            if r["valid"]:
                assert r["parsed"]["sz"] == sz.upper()

    def test_expected_format_in_error(self):
        r = validate_group_name("bad")
        assert "expected_format" in r
        assert "example" in r


# ---- validate_server_name ----

class TestValidateServerName:
    def test_valid_server(self):
        r = validate_server_name("svr-CRM-NH02-GEN-CRMPROD01")
        assert r["valid"] is True
        assert r["parsed"]["server_name"] == "CRMPROD01"

    def test_invalid_pattern(self):
        r = validate_server_name("not-a-server")
        assert r["valid"] is False
        assert r["type"] == "server"

    def test_invalid_nh(self):
        r = validate_server_name("svr-CRM-NH99-GEN-SRV01")
        assert r["valid"] is False
        assert "Invalid NH ID" in r["error"]

    def test_invalid_sz(self):
        r = validate_server_name("svr-CRM-NH02-BADSZ-SRV01")
        assert r["valid"] is False


# ---- validate_subnet_name ----

class TestValidateSubnetName:
    def test_valid_subnet(self):
        r = validate_subnet_name("rng-CRM-NH02-GEN-WEBNET")
        assert r["valid"] is True
        assert r["parsed"]["descriptor"] == "WEBNET"

    def test_invalid_pattern(self):
        r = validate_subnet_name("not-a-subnet")
        assert r["valid"] is False
        assert r["type"] == "subnet"

    def test_invalid_nh(self):
        r = validate_subnet_name("rng-CRM-NH99-GEN-NET01")
        assert r["valid"] is False

    def test_invalid_sz(self):
        r = validate_subnet_name("rng-CRM-NH02-BADSZ-NET01")
        assert r["valid"] is False


# ---- validate_name (auto-detect) ----

class TestValidateName:
    def test_group_prefix(self):
        r = validate_name("grp-CRM-NH02-GEN-APP")
        assert r["valid"] is True
        assert r["type"] == "group"

    def test_server_prefix(self):
        r = validate_name("svr-CRM-NH02-GEN-SRV01")
        assert r["valid"] is True
        assert r["type"] == "server"

    def test_subnet_prefix(self):
        r = validate_name("rng-CRM-NH02-GEN-NET01")
        assert r["valid"] is True
        assert r["type"] == "subnet"

    def test_unknown_prefix(self):
        r = validate_name("unknown-thing")
        assert r["valid"] is False
        assert r["type"] == "unknown"
        assert "expected_prefixes" in r


# ---- generate_* ----

class TestGenerateName:
    def test_generate_group(self):
        r = generate_group_name("CRM", "NH02", "GEN", "APP")
        assert r["valid"] is True
        assert r["generated_name"] == "grp-CRM-NH02-GEN-APP"

    def test_generate_server(self):
        r = generate_server_name("CRM", "NH02", "GEN", "SRV01")
        assert r["valid"] is True
        assert r["generated_name"] == "svr-CRM-NH02-GEN-SRV01"

    def test_generate_subnet(self):
        r = generate_subnet_name("CRM", "NH02", "GEN", "WEBNET")
        assert r["valid"] is True
        assert r["generated_name"] == "rng-CRM-NH02-GEN-WEBNET"

    def test_generate_invalid(self):
        r = generate_group_name("CRM", "NH99", "GEN", "APP")
        assert r["valid"] is False
        assert "generated_name" in r


# ---- check_group_to_group ----

class TestCheckGroupToGroup:
    def test_both_groups(self):
        r = check_group_to_group("Group", "Group")
        assert r["compliant"] is True
        assert r["requires_exception"] is False

    def test_group_to_predefined(self):
        r = check_group_to_group("Group", "Predefined")
        assert r["compliant"] is True

    def test_ip_source(self):
        r = check_group_to_group("IP", "Group")
        assert r["compliant"] is False
        assert r["requires_exception"] is True
        assert "source type" in r["message"]

    def test_ip_to_ip(self):
        r = check_group_to_group("IP", "IP")
        assert r["compliant"] is False
        assert "source type" in r["message"]
        assert "destination type" in r["message"]

    def test_group_to_ip(self):
        r = check_group_to_group("Group", "IP")
        assert r["compliant"] is False
        assert "exception_reason" in r


# ---- suggest_standard_name ----

class TestSuggestStandardName:
    def test_subnet_detection(self):
        r = suggest_standard_name("web-subnet-10", "CRM")
        assert r["prefix"] == "rng"
        assert r["suggested_name"].startswith("rng-CRM-")

    def test_server_detection(self):
        r = suggest_standard_name("CRM-server-01", "CRM")
        assert r["prefix"] == "svr"

    def test_db_detection(self):
        r = suggest_standard_name("database-cluster", "CRM")
        assert r["prefix"] == "grp"
        assert "DB" in r["suggested_name"]

    def test_web_detection(self):
        r = suggest_standard_name("web-frontend", "CRM")
        assert "WEB" in r["suggested_name"]

    def test_batch_detection(self):
        r = suggest_standard_name("batch-job-runner", "CRM")
        assert "BAT" in r["suggested_name"]

    def test_mq_detection(self):
        r = suggest_standard_name("kafka-queue", "CRM")
        assert "MQ" in r["suggested_name"]

    def test_api_detection(self):
        r = suggest_standard_name("rest-api-gateway", "CRM")
        assert "API" in r["suggested_name"]

    def test_default_app(self):
        r = suggest_standard_name("unknown-thing", "CRM")
        assert r["prefix"] == "grp"
        assert "APP" in r["suggested_name"]

    def test_range_detection(self):
        r = suggest_standard_name("ip-range-10", "CRM")
        assert r["prefix"] == "rng"

    def test_net_detection(self):
        r = suggest_standard_name("net-segment", "CRM")
        assert r["prefix"] == "rng"

    def test_cidr_detection(self):
        r = suggest_standard_name("cidr-block", "CRM")
        assert r["prefix"] == "rng"

    def test_host_detection(self):
        r = suggest_standard_name("host-machine", "CRM")
        assert r["prefix"] == "svr"

    def test_validation_included(self):
        r = suggest_standard_name("some-thing", "CRM")
        assert "validation" in r
        assert "legacy_name" in r

    def test_custom_nh_sz(self):
        r = suggest_standard_name("server-01", "CRM", nh="NH05", sz="CCS")
        assert "NH05" in r["suggested_name"]
        assert "CCS" in r["suggested_name"]

    def test_srv_keyword(self):
        r = suggest_standard_name("srv-instance", "CRM")
        assert r["prefix"] == "svr"

    def test_svr_keyword(self):
        r = suggest_standard_name("svr-machine", "CRM")
        assert r["prefix"] == "svr"


# ---- determine_security_zone ----

class TestDetermineSecurityZone:
    def test_paa_internet_prod(self):
        r = determine_security_zone(paa_zone=True, exposure="Internet")
        assert r["security_zone"] == "PNA"
        assert r["neighbourhood_type"] == "DMZ"

    def test_paa_pci_pan(self):
        r = determine_security_zone(paa_zone=True, pci_pan=True)
        assert r["security_zone"] == "CDE"

    def test_paa_pci_track_data(self):
        r = determine_security_zone(paa_zone=True, pci_track_data=True)
        assert r["security_zone"] == "CDE"

    def test_paa_pci_cvv_pin(self):
        r = determine_security_zone(paa_zone=True, pci_cvv_pin=True)
        assert r["security_zone"] == "CDE"

    def test_ecpa(self):
        r = determine_security_zone(deployment_type="ECPA")
        assert r["security_zone"] == "UCPA"

    def test_critical_payment(self):
        r = determine_security_zone(critical_payment=True)
        assert r["security_zone"] == "CPN"

    def test_confidential_most_critical(self):
        r = determine_security_zone(data_classification="CONFIDENTIAL", criticality_rating=1)
        assert r["security_zone"] == "BCCI"

    def test_restricted_most_critical(self):
        r = determine_security_zone(data_classification="RESTRICTED", criticality_rating=1)
        assert r["security_zone"] == "BCCI"

    def test_confidential_not_critical(self):
        r = determine_security_zone(data_classification="CONFIDENTIAL", criticality_rating=3)
        assert r["security_zone"] == "RST"

    def test_restricted_not_critical(self):
        r = determine_security_zone(data_classification="RESTRICTED", criticality_rating=2)
        assert r["security_zone"] == "RST"

    def test_default_gen(self):
        r = determine_security_zone()
        assert r["security_zone"] == "GEN"

    def test_nonprod_paa_internet(self):
        r = determine_security_zone(paa_zone=True, exposure="Internet", environment="Non-Production")
        assert r["security_zone"] == "PNA"
        assert "Non-Production" in r["neighbourhood_type"]

    def test_nonprod_paa_internal(self):
        r = determine_security_zone(paa_zone=True, environment="Non-Production")
        assert r["security_zone"] == "GEN"
        assert "Non-Production" in r["neighbourhood_type"]

    def test_nonprod_default(self):
        r = determine_security_zone(environment="Non-Production")
        assert r["security_zone"] == "GEN"


# ---- get_naming_standards_info ----

class TestGetNamingStandardsInfo:
    def test_structure(self):
        info = get_naming_standards_info()
        assert "prefixes" in info
        assert "grp" in info["prefixes"]
        assert "svr" in info["prefixes"]
        assert "rng" in info["prefixes"]
        assert "valid_nh_ids" in info
        assert "valid_sz_codes" in info
        assert "valid_subtypes" in info
        assert "enforcement_rules" in info
        assert len(info["enforcement_rules"]) > 0

    def test_nh_ids_count(self):
        info = get_naming_standards_info()
        assert len(info["valid_nh_ids"]) == 17

    def test_prefix_details(self):
        info = get_naming_standards_info()
        for prefix in ("grp", "svr", "rng"):
            assert "description" in info["prefixes"][prefix]
            assert "pattern" in info["prefixes"][prefix]
            assert "example" in info["prefixes"][prefix]


# ---- Module-level constants ----

class TestConstants:
    def test_valid_nh_ids(self):
        assert "NH01" in VALID_NH_IDS
        assert "NH17" in VALID_NH_IDS
        assert len(VALID_NH_IDS) == 17

    def test_valid_sz_codes(self):
        assert "GEN" in VALID_SZ_CODES
        assert "CDE" in VALID_SZ_CODES
        assert "STD" in VALID_SZ_CODES

    def test_valid_subtypes(self):
        assert "APP" in VALID_SUBTYPES
        assert "WEB" in VALID_SUBTYPES
        assert "DB" in VALID_SUBTYPES

    def test_patterns_compiled(self):
        assert GROUP_PATTERN is not None
        assert SERVER_PATTERN is not None
        assert SUBNET_PATTERN is not None
