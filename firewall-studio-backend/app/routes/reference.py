from fastapi import APIRouter, HTTPException, UploadFile, File
from app.database import (
    get_ngdc_datacenters, get_security_zones, get_predefined_destinations,
    get_neighbourhoods, get_legacy_datacenters, get_applications,
    get_environments, get_chg_requests, get_naming_standards, get_org_config,
    get_policy_matrix, get_heritage_dc_matrix, get_ngdc_prod_matrix, get_nonprod_matrix,
    get_rules, get_legacy_rules, update_legacy_rule, delete_legacy_rule,
    import_legacy_rules, get_migration_history, migrate_rule_to_ngdc,
    create_migration_review,
    create_neighbourhood, update_neighbourhood, delete_neighbourhood,
    create_security_zone, update_security_zone, delete_security_zone,
    create_application, update_application, delete_application,
    create_datacenter, update_datacenter, delete_datacenter,
    create_predefined_destination, update_predefined_destination, delete_predefined_destination,
    create_environment, delete_environment,
    update_org_config, update_naming_standards,
    create_policy_entry, delete_policy_entry,
    create_chg_request,
    get_groups, get_group, create_group, update_group, delete_group,
    add_group_member, remove_group_member,
    create_rule_modification, get_rule_modifications, approve_rule_modification, reject_rule_modification,
    compile_legacy_rule, validate_birthright,
    get_birthright_matrix, update_birthright_matrix, add_birthright_entry, delete_birthright_entry,
    get_ngdc_recommendations,
)
import io
import openpyxl
from app.services.naming_standards import (
    validate_name, generate_group_name, generate_server_name,
    generate_subnet_name, suggest_standard_name, determine_security_zone,
    get_naming_standards_info,
)

router = APIRouter(prefix="/api/reference", tags=["Reference Data"])


# ---- Read endpoints ----

@router.get("/ngdc-datacenters")
async def list_ngdc_datacenters():
    """Return NGDC datacenters enriched with full neighbourhood objects for the UI.

    The raw JSON stores neighbourhoods as ID strings (e.g. ["NH01","NH02"]).
    The frontend NGDCSidebar expects objects: {name, subnets: string[]}.
    This endpoint resolves those IDs and also computes rule_count + ip_groups.
    """
    raw_dcs = await get_ngdc_datacenters()
    all_nhs = await get_neighbourhoods()
    all_rules = await get_rules()
    nh_lookup: dict[str, dict] = {nh["nh_id"]: nh for nh in all_nhs}

    enriched = []
    for dc in raw_dcs:
        dc_code = dc.get("code", "")
        # Resolve neighbourhood IDs to objects with subnets filtered to this DC
        nh_ids = dc.get("neighbourhoods", [])
        resolved_nhs = []
        ip_groups: list[dict] = []
        for nh_id in nh_ids:
            if isinstance(nh_id, str):
                nh_data = nh_lookup.get(nh_id)
                if nh_data:
                    # Filter IP ranges to those belonging to this DC
                    dc_ranges = [r for r in nh_data.get("ip_ranges", []) if r.get("dc") == dc_code]
                    subnets = [r["cidr"] for r in dc_ranges]
                    resolved_nhs.append({
                        "name": f"{nh_id} - {nh_data.get('name', '')}",
                        "nh_id": nh_id,
                        "security_zones": nh_data.get("security_zones", []),
                        "subnets": subnets,
                    })
                    # Also build ip_groups entries
                    if dc_ranges:
                        ip_groups.append({
                            "name": f"{nh_id} Groups",
                            "entries": [
                                {"name": r.get("description", r["cidr"]), "cidr": r["cidr"]}
                                for r in dc_ranges
                            ],
                        })
                else:
                    resolved_nhs.append({"name": nh_id, "nh_id": nh_id, "zone": "", "subnets": []})
            elif isinstance(nh_id, dict):
                # Already an object – ensure subnets key exists
                if "subnets" not in nh_id:
                    nh_id["subnets"] = []
                resolved_nhs.append(nh_id)

        # Count rules assigned to this DC
        rule_count = sum(1 for r in all_rules if r.get("datacenter") == dc_code)

        enriched.append({
            **dc,
            "neighbourhoods": resolved_nhs,
            "ip_groups": ip_groups,
            "rule_count": rule_count,
        })
    return enriched


@router.get("/security-zones")
async def list_security_zones():
    return await get_security_zones()


@router.get("/predefined-destinations")
async def list_predefined_destinations():
    return await get_predefined_destinations()


@router.get("/neighbourhoods")
async def list_neighbourhoods():
    return await get_neighbourhoods()


@router.get("/legacy-datacenters")
async def list_legacy_datacenters():
    return await get_legacy_datacenters()


@router.get("/applications")
async def list_applications():
    return await get_applications()


@router.get("/environments")
async def list_environments():
    return await get_environments()


@router.get("/chg-requests")
async def list_chg_requests():
    return await get_chg_requests()


@router.post("/chg-requests")
async def create_new_chg_request(data: dict):
    return await create_chg_request(data)


@router.get("/org-config")
async def get_org_config_endpoint():
    config = await get_org_config()
    if not config:
        raise HTTPException(status_code=404, detail="Org config not found")
    return config


@router.get("/policy-matrix")
async def list_policy_matrix():
    return await get_policy_matrix()


@router.get("/policy-matrix/heritage-dc")
async def list_heritage_dc_matrix():
    return await get_heritage_dc_matrix()


@router.get("/policy-matrix/ngdc-prod")
async def list_ngdc_prod_matrix():
    return await get_ngdc_prod_matrix()


@router.get("/policy-matrix/nonprod")
async def list_nonprod_matrix():
    return await get_nonprod_matrix()


@router.get("/policy-matrix/all")
async def list_all_policy_matrices():
    return {
        "heritage_dc": await get_heritage_dc_matrix(),
        "ngdc_prod": await get_ngdc_prod_matrix(),
        "nonprod": await get_nonprod_matrix(),
        "combined": await get_policy_matrix(),
    }


@router.get("/naming-standards")
async def list_naming_standards():
    return get_naming_standards_info()


# ---- Naming Standards utilities ----

@router.post("/naming-standards/validate")
async def validate_naming(data: dict):
    name = data.get("name", "")
    return validate_name(name)


@router.post("/naming-standards/generate")
async def generate_name(data: dict):
    name_type = data.get("type", "group")
    app_id = data.get("app_id", "")
    nh = data.get("nh", "NH01")
    sz = data.get("sz", "GEN")
    if name_type == "group":
        subtype = data.get("subtype", "APP")
        return generate_group_name(app_id, nh, sz, subtype)
    elif name_type == "server":
        server_name = data.get("server_name", "SRV01")
        return generate_server_name(app_id, nh, sz, server_name)
    elif name_type == "subnet":
        descriptor = data.get("descriptor", "NET")
        return generate_subnet_name(app_id, nh, sz, descriptor)
    return {"error": "Invalid type. Use 'group', 'server', or 'subnet'"}


@router.post("/naming-standards/suggest")
async def suggest_name(data: dict):
    legacy_name = data.get("legacy_name", "")
    app_id = data.get("app_id", "APP")
    nh = data.get("nh", "NH01")
    sz = data.get("sz", "GEN")
    return suggest_standard_name(legacy_name, app_id, nh, sz)


@router.post("/naming-standards/determine-zone")
async def determine_zone(data: dict):
    return determine_security_zone(
        paa_zone=data.get("paa_zone", False),
        exposure=data.get("exposure", "Internal"),
        pci_pan=data.get("pci_pan", False),
        pci_track_data=data.get("pci_track_data", False),
        pci_cvv_pin=data.get("pci_cvv_pin", False),
        deployment_type=data.get("deployment_type", "ON_PREMISE"),
        critical_payment=data.get("critical_payment", False),
        data_classification=data.get("data_classification", "INTERNAL"),
        criticality_rating=data.get("criticality_rating", 3),
        environment=data.get("environment", "Production"),
    )


# ---- CRUD: Neighbourhoods ----

@router.post("/neighbourhoods")
async def create_nh(data: dict):
    return await create_neighbourhood(data)


@router.put("/neighbourhoods/{nh_id}")
async def update_nh(nh_id: str, data: dict):
    result = await update_neighbourhood(nh_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Neighbourhood not found")
    return result


@router.delete("/neighbourhoods/{nh_id}")
async def delete_nh(nh_id: str):
    if not await delete_neighbourhood(nh_id):
        raise HTTPException(status_code=404, detail="Neighbourhood not found")
    return {"message": "Neighbourhood deleted"}


# ---- CRUD: Security Zones ----

@router.post("/security-zones")
async def create_sz(data: dict):
    return await create_security_zone(data)


@router.put("/security-zones/{code}")
async def update_sz(code: str, data: dict):
    result = await update_security_zone(code, data)
    if not result:
        raise HTTPException(status_code=404, detail="Security zone not found")
    return result


@router.delete("/security-zones/{code}")
async def delete_sz(code: str):
    if not await delete_security_zone(code):
        raise HTTPException(status_code=404, detail="Security zone not found")
    return {"message": "Security zone deleted"}


# ---- CRUD: Applications ----

@router.post("/applications")
async def create_app(data: dict):
    return await create_application(data)


@router.put("/applications/{app_id}")
async def update_app(app_id: str, data: dict):
    result = await update_application(app_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Application not found")
    return result


@router.delete("/applications/{app_id}")
async def delete_app(app_id: str):
    if not await delete_application(app_id):
        raise HTTPException(status_code=404, detail="Application not found")
    return {"message": "Application deleted"}


# ---- CRUD: Datacenters ----

@router.post("/ngdc-datacenters")
async def create_ngdc_dc(data: dict):
    return await create_datacenter(data, "ngdc")


@router.put("/ngdc-datacenters/{code}")
async def update_ngdc_dc(code: str, data: dict):
    result = await update_datacenter(code, data, "ngdc")
    if not result:
        raise HTTPException(status_code=404, detail="Datacenter not found")
    return result


@router.delete("/ngdc-datacenters/{code}")
async def delete_ngdc_dc(code: str):
    if not await delete_datacenter(code, "ngdc"):
        raise HTTPException(status_code=404, detail="Datacenter not found")
    return {"message": "Datacenter deleted"}


@router.post("/legacy-datacenters")
async def create_legacy_dc(data: dict):
    return await create_datacenter(data, "legacy")


@router.put("/legacy-datacenters/{code}")
async def update_legacy_dc(code: str, data: dict):
    result = await update_datacenter(code, data, "legacy")
    if not result:
        raise HTTPException(status_code=404, detail="Legacy datacenter not found")
    return result


@router.delete("/legacy-datacenters/{code}")
async def delete_legacy_dc(code: str):
    if not await delete_datacenter(code, "legacy"):
        raise HTTPException(status_code=404, detail="Legacy datacenter not found")
    return {"message": "Legacy datacenter deleted"}


# ---- CRUD: Predefined Destinations ----

@router.post("/predefined-destinations")
async def create_dest(data: dict):
    return await create_predefined_destination(data)


@router.put("/predefined-destinations/{name}")
async def update_dest(name: str, data: dict):
    result = await update_predefined_destination(name, data)
    if not result:
        raise HTTPException(status_code=404, detail="Destination not found")
    return result


@router.delete("/predefined-destinations/{name}")
async def delete_dest(name: str):
    if not await delete_predefined_destination(name):
        raise HTTPException(status_code=404, detail="Destination not found")
    return {"message": "Destination deleted"}


# ---- CRUD: Environments ----

@router.post("/environments")
async def create_env(data: dict):
    return await create_environment(data)


@router.delete("/environments/{code}")
async def delete_env(code: str):
    if not await delete_environment(code):
        raise HTTPException(status_code=404, detail="Environment not found")
    return {"message": "Environment deleted"}


# ---- CRUD: Org Config ----

@router.put("/org-config")
async def update_org(data: dict):
    result = await update_org_config(data)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to update org config")
    return result


# ---- CRUD: Naming Standards ----

@router.put("/naming-standards")
async def update_standards(data: dict):
    result = await update_naming_standards(data)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to update naming standards")
    return result


# ---- CRUD: Policy Matrix ----

@router.post("/policy-matrix")
async def create_policy(data: dict):
    return await create_policy_entry(data)


@router.delete("/policy-matrix/{source_zone}/{dest_zone}")
async def delete_policy(source_zone: str, dest_zone: str):
    if not await delete_policy_entry(source_zone, dest_zone):
        raise HTTPException(status_code=404, detail="Policy entry not found")
    return {"message": "Policy entry deleted"}


# ---- CRUD: Groups ----

@router.get("/groups")
async def list_groups(app_id: str | None = None):
    groups = await get_groups()
    if app_id:
        groups = [g for g in groups if g.get("app_id") == app_id]
    return groups


@router.get("/groups/{name:path}")
async def get_group_endpoint(name: str):
    group = await get_group(name)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@router.post("/groups")
async def create_new_group(data: dict):
    return await create_group(data)


@router.put("/groups/{name:path}")
async def update_existing_group(name: str, data: dict):
    result = await update_group(name, data)
    if not result:
        raise HTTPException(status_code=404, detail="Group not found")
    return result


@router.delete("/groups/{name:path}")
async def delete_existing_group(name: str):
    if not await delete_group(name):
        raise HTTPException(status_code=404, detail="Group not found")
    return {"message": "Group deleted"}


@router.post("/groups/{name:path}/members")
async def add_member_to_group(name: str, data: dict):
    result = await add_group_member(name, data)
    if not result:
        raise HTTPException(status_code=404, detail="Group not found")
    return result


@router.delete("/groups/{name:path}/members/{member_value}")
async def remove_member_from_group(name: str, member_value: str):
    result = await remove_group_member(name, member_value)
    if not result:
        raise HTTPException(status_code=404, detail="Group or member not found")
    return result


# ---- Legacy Rules (for Migration Studio & Firewall Management) ----

@router.get("/legacy-rules")
async def list_legacy_rules(app_id: str | None = None, exclude_migrated: bool = False):
    rules = await get_legacy_rules()
    if app_id:
        rules = [r for r in rules if str(r.get("app_id")) == str(app_id) or r.get("app_distributed_id") == app_id]
    if exclude_migrated:
        rules = [r for r in rules if r.get("migration_status") != "Completed"]
    return rules


@router.get("/legacy-rules/{rule_id}")
async def get_legacy_rule_detail(rule_id: str):
    rules = await get_legacy_rules()
    rule = next((r for r in rules if r["id"] == rule_id), None)
    if not rule:
        raise HTTPException(status_code=404, detail="Legacy rule not found")
    return rule


@router.put("/legacy-rules/{rule_id}")
async def update_legacy_rule_endpoint(rule_id: str, data: dict):
    result = await update_legacy_rule(rule_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Legacy rule not found")
    return result


@router.delete("/legacy-rules/{rule_id}")
async def delete_legacy_rule_endpoint(rule_id: str):
    ok = await delete_legacy_rule(rule_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Legacy rule not found")
    return {"message": "Deleted"}


@router.post("/legacy-rules/import")
async def import_legacy_rules_excel(file: UploadFile = File(...)):
    """Import legacy rules from an Excel (.xlsx) file with deduplication."""
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")
    contents = await file.read()
    wb = openpyxl.load_workbook(io.BytesIO(contents))
    ws = wb.active
    if ws is None:
        raise HTTPException(status_code=400, detail="Empty workbook")
    headers = [cell.value for cell in ws[1]]
    col_map = {
        "App ID": "app_id", "App Current Distributed ID": "app_distributed_id",
        "App Name": "app_name", "Inventory Item": "inventory_item",
        "Policy Name": "policy_name", "Rule Global": "rule_global",
        "Rule Action": "rule_action", "Rule Source": "rule_source",
        "Rule Source Expanded": "rule_source_expanded", "Rule Source Zone": "rule_source_zone",
        "Rule Destination": "rule_destination",
        "Rule Destination Expanded": "rule_destination_expanded",
        "Rule Destination Zone": "rule_destination_zone",
        "Rule Service": "rule_service", "Rule Service Expanded": "rule_service_expanded",
        "RN": "rn", "RC": "rc",
    }
    parsed_rules = []
    for row_idx in range(2, ws.max_row + 1):
        row_vals = [cell.value for cell in ws[row_idx]]
        if not any(row_vals):
            continue
        rule: dict = {}
        for i, h in enumerate(headers):
            if h in col_map and i < len(row_vals):
                val = row_vals[i]
                rule[col_map[h]] = val if val is not None else ""
        rule["is_standard"] = False
        rule["migration_status"] = "Not Started"
        parsed_rules.append(rule)
    result = await import_legacy_rules(parsed_rules)
    return result


@router.post("/legacy-rules/migrate")
async def migrate_rules_to_ngdc(data: dict):
    """Migrate selected rules to NGDC standards."""
    rule_ids = data.get("rule_ids", [])
    if not rule_ids:
        raise HTTPException(status_code=400, detail="rule_ids required")
    migrated = []
    for rid in rule_ids:
        result = await migrate_rule_to_ngdc(rid)
        if result:
            migrated.append(result)
    return {"migrated": len(migrated), "rules": migrated}


@router.post("/legacy-rules/submit-for-review")
async def submit_legacy_rules_for_review(data: dict):
    """Submit selected legacy rules for migration review."""
    rule_ids = data.get("rule_ids", [])
    comments = data.get("comments", "")
    if not rule_ids:
        raise HTTPException(status_code=400, detail="rule_ids required")
    reviews = await create_migration_review(rule_ids, comments)
    return {"submitted": len(reviews), "reviews": reviews}


@router.get("/migration-history")
async def list_migration_history():
    return await get_migration_history()


@router.get("/legacy-rules/migrated")
async def list_migrated_rules():
    """Return only rules that have been migrated to NGDC (for Firewall Studio)."""
    rules = await get_legacy_rules()
    return [r for r in rules if r.get("migration_status") == "Completed"]


# ---- Rule Modification with Delta Tracking ----

@router.post("/legacy-rules/{rule_id}/modify")
async def modify_legacy_rule(rule_id: str, data: dict):
    """Create a rule modification request with delta tracking."""
    modifications = data.get("modifications", {})
    comments = data.get("comments", "")
    result = await create_rule_modification(rule_id, modifications, comments)
    if not result:
        raise HTTPException(status_code=404, detail="Legacy rule not found")
    return result


@router.get("/rule-modifications")
async def list_rule_modifications(rule_id: str | None = None):
    return await get_rule_modifications(rule_id)


@router.post("/rule-modifications/{mod_id}/approve")
async def approve_mod(mod_id: str, data: dict):
    notes = data.get("notes", "")
    result = await approve_rule_modification(mod_id, notes)
    if not result:
        raise HTTPException(status_code=404, detail="Modification not found")
    return result


@router.post("/rule-modifications/{mod_id}/reject")
async def reject_mod(mod_id: str, data: dict):
    notes = data.get("notes", "")
    if not notes:
        raise HTTPException(status_code=400, detail="Rejection notes required")
    result = await reject_rule_modification(mod_id, notes)
    if not result:
        raise HTTPException(status_code=404, detail="Modification not found")
    return result


# ---- Legacy Rule Compiler ----

@router.post("/legacy-rules/{rule_id}/compile")
async def compile_legacy(rule_id: str, vendor: str = "generic"):
    result = await compile_legacy_rule(rule_id, vendor)
    if not result:
        raise HTTPException(status_code=404, detail="Legacy rule not found")
    return result


# ---- NGDC Recommendations ----

@router.get("/legacy-rules/{rule_id}/ngdc-recommendations")
async def get_recommendations(rule_id: str):
    result = await get_ngdc_recommendations(rule_id)
    if not result:
        raise HTTPException(status_code=404, detail="Legacy rule not found")
    return result


# ---- Birthright Validation ----

@router.post("/birthright/validate")
async def validate_birthright_rule(data: dict):
    return await validate_birthright(data)


@router.get("/birthright/matrix")
async def get_birthright_matrices():
    return await get_birthright_matrix()


@router.put("/birthright/matrix/{matrix_type}")
async def update_matrix(matrix_type: str, data: dict):
    entries = data.get("entries", [])
    result = await update_birthright_matrix(matrix_type, entries)
    if not result and result != []:
        raise HTTPException(status_code=400, detail="Invalid matrix type")
    return result


@router.post("/birthright/matrix/{matrix_type}")
async def add_matrix_entry(matrix_type: str, data: dict):
    return await add_birthright_entry(matrix_type, data)


@router.delete("/birthright/matrix/{matrix_type}/{index}")
async def delete_matrix_entry(matrix_type: str, index: int):
    if not await delete_birthright_entry(matrix_type, index):
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"message": "Entry deleted"}


# ---- Legacy-to-NGDC Organization Mappings ----

@router.get("/ngdc-mappings")
async def list_ngdc_mappings():
    from app.database import get_ngdc_mappings
    return await get_ngdc_mappings()


@router.post("/ngdc-mappings")
async def create_ngdc_mapping(data: dict):
    from app.database import add_ngdc_mapping
    return await add_ngdc_mapping(data)


@router.put("/ngdc-mappings/{mapping_id}")
async def update_ngdc_mapping_endpoint(mapping_id: str, data: dict):
    from app.database import update_ngdc_mapping
    result = await update_ngdc_mapping(mapping_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return result


@router.delete("/ngdc-mappings/{mapping_id}")
async def delete_ngdc_mapping_endpoint(mapping_id: str):
    from app.database import delete_ngdc_mapping
    ok = await delete_ngdc_mapping(mapping_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return {"message": "Mapping deleted"}


@router.post("/ngdc-mappings/import")
async def import_ngdc_mappings_excel(file: UploadFile = File(...)):
    """Import legacy-to-NGDC mappings from Excel."""
    from app.database import import_ngdc_mappings
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")
    contents = await file.read()
    wb = openpyxl.load_workbook(io.BytesIO(contents))
    ws = wb.active
    if ws is None:
        raise HTTPException(status_code=400, detail="Empty workbook")
    headers = [cell.value for cell in ws[1]]
    mappings = []
    for row_idx in range(2, ws.max_row + 1):
        row_vals = [cell.value for cell in ws[row_idx]]
        if not any(row_vals):
            continue
        m: dict = {}
        for i, h in enumerate(headers):
            if i < len(row_vals) and h:
                m[str(h).lower().replace(" ", "_")] = row_vals[i] if row_vals[i] is not None else ""
        mappings.append(m)
    result = await import_ngdc_mappings(mappings)
    return result


@router.post("/ngdc-mappings/bulk")
async def bulk_save_ngdc_mappings(data: dict):
    """Save all mappings at once (from org admin)."""
    from app.database import save_ngdc_mappings
    mappings = data.get("mappings", [])
    return await save_ngdc_mappings(mappings)


# ---- Group Provisioning to Firewall Device ----

@router.post("/groups/provision/{app_id}")
async def provision_groups(app_id: str, data: dict):
    """Provision groups for an app to the firewall device (NGDC standards enforced)."""
    from app.database import provision_groups_to_device
    device_type = data.get("device_type", "palo_alto")
    return await provision_groups_to_device(app_id, device_type)


@router.get("/provisioning-history")
async def list_provisioning_history(app_id: str | None = None):
    from app.database import get_provisioning_history
    return await get_provisioning_history(app_id)


# ---- Enhanced Compile with Group Expansion ----

@router.post("/rules/{rule_id}/compile-expanded")
async def compile_rule_expanded(rule_id: str, data: dict):
    from app.database import compile_rule_with_expansion
    vendor = data.get("vendor", "generic")
    expand = data.get("expand_groups", True)
    result = await compile_rule_with_expansion(rule_id, vendor, expand)
    if not result:
        raise HTTPException(status_code=404, detail="Rule not found")
    return result


# ---- App-to-DC/NH/SZ Mapping (Organization Reference) ----

@router.get("/app-dc-mappings")
async def list_app_dc_mappings():
    from app.database import get_app_dc_mappings
    return await get_app_dc_mappings()


@router.get("/app-dc-mappings/{app_id}")
async def get_app_dc_mapping(app_id: str):
    from app.database import get_app_dc_mapping_by_app
    result = await get_app_dc_mapping_by_app(app_id)
    if not result:
        raise HTTPException(status_code=404, detail="App DC mapping not found")
    return result


@router.post("/app-dc-mappings")
async def create_app_dc_mapping(data: dict):
    from app.database import add_app_dc_mapping
    return await add_app_dc_mapping(data)


@router.put("/app-dc-mappings/{mapping_id}")
async def update_app_dc_mapping_endpoint(mapping_id: str, data: dict):
    from app.database import update_app_dc_mapping
    result = await update_app_dc_mapping(mapping_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return result


@router.delete("/app-dc-mappings/{mapping_id}")
async def delete_app_dc_mapping_endpoint(mapping_id: str):
    from app.database import delete_app_dc_mapping
    ok = await delete_app_dc_mapping(mapping_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return {"message": "Mapping deleted"}


@router.post("/app-dc-mappings/import")
async def import_app_dc_mappings_excel(file: UploadFile = File(...)):
    """Import App-to-DC/NH/SZ mappings from Excel."""
    from app.database import import_app_dc_mappings
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")
    contents = await file.read()
    wb = openpyxl.load_workbook(io.BytesIO(contents))
    ws = wb.active
    if ws is None:
        raise HTTPException(status_code=400, detail="Empty workbook")
    headers = [cell.value for cell in ws[1]]
    mappings = []
    for row_idx in range(2, ws.max_row + 1):
        row_vals = [cell.value for cell in ws[row_idx]]
        if not any(row_vals):
            continue
        m: dict = {}
        for i, h in enumerate(headers):
            if i < len(row_vals) and h:
                key = str(h).lower().replace(" ", "_")
                m[key] = row_vals[i] if row_vals[i] is not None else ""
        mappings.append(m)
    result = await import_app_dc_mappings(mappings)
    return result


@router.post("/app-dc-mappings/bulk")
async def bulk_save_app_dc_mappings(data: dict):
    from app.database import save_app_dc_mappings
    mappings = data.get("mappings", [])
    return await save_app_dc_mappings(mappings)


# ---- NGDC Compliance Check ----

@router.post("/legacy-rules/check-compliance")
async def check_compliance(data: dict):
    """Check NGDC compliance for a single rule or batch of rules."""
    from app.database import check_ngdc_compliance, get_legacy_rules
    rule_ids = data.get("rule_ids", [])
    if not rule_ids:
        raise HTTPException(status_code=400, detail="rule_ids required")
    rules = await get_legacy_rules()
    results = []
    for rid in rule_ids:
        rule = next((r for r in rules if r["id"] == rid), None)
        if rule:
            result = await check_ngdc_compliance(rule)
            results.append(result)
    return results


# ---- Duplicate Detection ----

@router.post("/check-duplicates")
async def check_dups(data: dict):
    """Check for duplicate rules based on source+destination+service."""
    from app.database import check_duplicates
    source = data.get("source", "")
    destination = data.get("destination", "")
    service = data.get("service", "")
    exclude_id = data.get("exclude_id", "")
    duplicates = await check_duplicates(source, destination, service, exclude_id)
    return {"duplicates": duplicates, "count": len(duplicates)}


# ---- Import Rules to NGDC Standardization (from Network Firewall Request) ----

@router.post("/legacy-rules/import-to-ngdc")
async def import_to_ngdc(data: dict):
    """Import rules from Network Firewall Request to NGDC Standardization by app IDs."""
    from app.database import import_rules_to_ngdc_standardization
    app_ids = data.get("app_ids", [])
    if not app_ids:
        raise HTTPException(status_code=400, detail="app_ids required")
    return await import_rules_to_ngdc_standardization(app_ids)


# ---- Auto-Import Compliant Rules to Firewall Studio ----

@router.post("/legacy-rules/auto-import-to-studio")
async def auto_import_to_studio():
    """Auto-import NGDC-compliant rules from Network Firewall Request into Firewall Studio."""
    from app.database import auto_import_compliant_rules_to_studio
    return await auto_import_compliant_rules_to_studio()


# ---- Expand Groups in Rule ----

@router.get("/legacy-rules/{rule_id}/expanded")
async def get_expanded_rule(rule_id: str):
    """Get a legacy rule with groups expanded to show all IPs/ranges."""
    from app.database import expand_groups_in_rule, get_legacy_rules
    rules = await get_legacy_rules()
    rule = next((r for r in rules if r["id"] == rule_id), None)
    if not rule:
        raise HTTPException(status_code=404, detail="Legacy rule not found")
    return await expand_groups_in_rule(rule)


# ---- Create Migration Group ----

@router.post("/migration-groups")
async def create_mig_group(data: dict):
    """Create a new group during migration with NGDC naming standards."""
    from app.database import create_migration_group
    name = data.get("name", "")
    app_id = data.get("app_id", "")
    members = data.get("members", [])
    nh = data.get("nh", "")
    sz = data.get("sz", "")
    if not name:
        raise HTTPException(status_code=400, detail="Group name required")
    return await create_migration_group(name, app_id, members, nh, sz)


# ---- IP Mappings (Legacy DC <-> NGDC one-to-one) ----

@router.get("/ip-mappings")
async def list_ip_mappings(legacy_dc: str | None = None, app_id: str | None = None):
    from app.database import get_ip_mappings
    return await get_ip_mappings(legacy_dc, app_id)


@router.post("/ip-mappings")
async def create_ip_mapping(data: dict):
    from app.database import add_ip_mapping
    return await add_ip_mapping(data)


@router.put("/ip-mappings/{mapping_id}")
async def update_ip_mapping_endpoint(mapping_id: str, data: dict):
    from app.database import update_ip_mapping
    result = await update_ip_mapping(mapping_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="IP mapping not found")
    return result


@router.delete("/ip-mappings/{mapping_id}")
async def delete_ip_mapping_endpoint(mapping_id: str):
    from app.database import delete_ip_mapping
    if not await delete_ip_mapping(mapping_id):
        raise HTTPException(status_code=404, detail="IP mapping not found")
    return {"message": "IP mapping deleted"}


@router.post("/ip-mappings/lookup")
async def lookup_ip_mapping(data: dict):
    """Look up the NGDC equivalent for a legacy IP address."""
    from app.database import lookup_ngdc_ip
    legacy_ip = data.get("legacy_ip", "")
    legacy_dc = data.get("legacy_dc", "")
    result = await lookup_ngdc_ip(legacy_ip, legacy_dc)
    if not result:
        return {"found": False, "message": f"No NGDC mapping found for {legacy_ip}"}
    return {"found": True, "mapping": result}


# ---- Firewall Boundary Analysis ----

@router.get("/firewall-boundaries")
async def get_firewall_boundaries(
    src_nh: str = "", src_sz: str = "", dst_nh: str = "", dst_sz: str = ""
):
    """Determine how many firewall boundaries a rule must cross based on
    the Logical Data Flow rules (NH/SZ placement)."""
    from app.database import determine_firewall_boundaries
    return await determine_firewall_boundaries(src_nh, src_sz, dst_nh, dst_sz)


@router.get("/logical-flow-rules")
async def get_logical_flow_rules():
    """Return the Logical Data Flow rule definitions."""
    from app.seed_data import LOGICAL_FLOW_RULES, SEGMENTED_ZONES
    return {"rules": LOGICAL_FLOW_RULES, "segmented_zones": list(SEGMENTED_ZONES)}


# ---- Egress/Ingress Compilation ----

@router.post("/compile/egress-ingress/{rule_id}")
async def compile_egress_ingress_endpoint(rule_id: str, vendor: str = "generic"):
    """Compile separate egress and ingress rules for cross-SZ combinations.
    Uses Logical Data Flow boundary analysis for device-specific compilation."""
    from app.database import compile_egress_ingress
    result = await compile_egress_ingress(rule_id, vendor)
    if not result:
        raise HTTPException(status_code=404, detail="Rule not found")
    return result


# ---- Resolved Policy Matrix ----

@router.get("/policy-matrix/resolved")
async def get_resolved_matrix(
    src_dc: str = "", src_nh: str = "", src_sz: str = "",
    dst_dc: str = "", dst_nh: str = "", dst_sz: str = "",
    environment: str = "Production",
):
    """Return policy matrix with Same/Any/Different resolved to real NH/SZ names."""
    from app.database import get_resolved_policy_matrix
    return await get_resolved_policy_matrix(src_dc, src_nh, src_sz, dst_dc, dst_nh, dst_sz, environment)


@router.get("/policy-matrix/preprod")
async def list_preprod_matrix():
    from app.database import get_preprod_matrix
    return await get_preprod_matrix()


# ---- Firewall Devices ----

@router.get("/firewall-devices")
async def list_firewall_devices():
    from app.database import get_firewall_devices
    return await get_firewall_devices()


@router.get("/firewall-devices/{device_id}")
async def get_firewall_device_endpoint(device_id: str):
    from app.database import get_firewall_device
    device = await get_firewall_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Firewall device not found")
    return device


@router.post("/firewall-devices")
async def create_firewall_device_endpoint(data: dict):
    from app.database import create_firewall_device
    return await create_firewall_device(data)


@router.put("/firewall-devices/{device_id}")
async def update_firewall_device_endpoint(device_id: str, data: dict):
    from app.database import update_firewall_device
    result = await update_firewall_device(device_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Firewall device not found")
    return result


@router.delete("/firewall-devices/{device_id}")
async def delete_firewall_device_endpoint(device_id: str):
    from app.database import delete_firewall_device
    ok = await delete_firewall_device(device_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Firewall device not found")
    return {"message": "Deleted"}


# ---- IP Mappings Import ----

@router.post("/ip-mappings/import")
async def import_ip_mappings_endpoint(data: dict):
    """Import multiple IP mappings at once, optionally for a specific app."""
    from app.database import import_ip_mappings
    records = data.get("mappings", [])
    app_id = data.get("app_id")
    return import_ip_mappings(records, app_id)


# ---- Firewall Device Patterns ----

@router.get("/firewall-device-patterns")
async def list_fw_device_patterns():
    """Return the generic firewall device naming patterns and DC vendor map."""
    from app.database import get_firewall_device_patterns, get_dc_vendor_map
    return {
        "patterns": await get_firewall_device_patterns(),
        "dc_vendor_map": await get_dc_vendor_map(),
    }


# ---- Standalone JSON Seed Export ----

@router.get("/export/seed-json")
async def export_seed_json():
    """Export all seed reference data as standalone JSON objects suitable for
    external consumption.  Returns neighbourhoods, security_zones, datacenters,
    policy_matrix (per environment), firewall device patterns, and
    app_dc_mappings in one payload."""
    from app.database import (
        get_neighbourhoods, get_security_zones, get_ngdc_datacenters,
        get_ngdc_prod_matrix, get_nonprod_matrix, get_preprod_matrix,
        get_app_dc_mappings, get_applications, get_firewall_devices,
        get_firewall_device_patterns, get_dc_vendor_map,
    )
    return {
        "neighbourhoods": await get_neighbourhoods(),
        "security_zones": await get_security_zones(),
        "datacenters": await get_ngdc_datacenters(),
        "policy_matrix": {
            "production": await get_ngdc_prod_matrix(),
            "non_production": await get_nonprod_matrix(),
            "pre_production": await get_preprod_matrix(),
        },
        "app_dc_mappings": await get_app_dc_mappings(),
        "applications": await get_applications(),
        "firewall_devices": await get_firewall_devices(),
        "firewall_device_patterns": await get_firewall_device_patterns(),
        "dc_vendor_map": await get_dc_vendor_map(),
    }
