from fastapi import APIRouter, HTTPException
from app.database import (
    get_ngdc_datacenters, get_security_zones, get_predefined_destinations,
    get_neighbourhoods, get_legacy_datacenters, get_applications,
    get_environments, get_chg_requests, get_naming_standards, get_org_config,
    get_policy_matrix, get_heritage_dc_matrix, get_ngdc_prod_matrix, get_nonprod_matrix,
    get_rules, get_legacy_rules, update_legacy_rule,
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
)
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


# ---- Legacy Rules (for Migration Studio) ----

@router.get("/legacy-rules")
async def list_legacy_rules(app_id: str | None = None):
    rules = await get_legacy_rules()
    if app_id:
        rules = [r for r in rules if r.get("app_id") == app_id]
    return rules


@router.put("/legacy-rules/{rule_id}")
async def update_legacy_rule_endpoint(rule_id: str, data: dict):
    result = await update_legacy_rule(rule_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Legacy rule not found")
    return result
