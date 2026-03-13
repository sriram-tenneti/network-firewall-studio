from fastapi import APIRouter
from app.database import (
    get_ngdc_datacenters, get_security_zones, get_predefined_destinations,
    get_neighbourhoods, get_legacy_datacenters, get_applications,
    get_environments, get_chg_requests, get_naming_standards,
)
from app.services.naming_standards import (
    validate_name, generate_group_name, generate_server_name,
    generate_subnet_name, suggest_standard_name, determine_security_zone,
    get_naming_standards_info,
)

router = APIRouter(prefix="/api/reference", tags=["Reference Data"])


@router.get("/ngdc-datacenters")
async def list_ngdc_datacenters():
    return get_ngdc_datacenters()


@router.get("/security-zones")
async def list_security_zones():
    return get_security_zones()


@router.get("/predefined-destinations")
async def list_predefined_destinations():
    return get_predefined_destinations()


@router.get("/neighbourhoods")
async def list_neighbourhoods():
    return get_neighbourhoods()


@router.get("/legacy-datacenters")
async def list_legacy_datacenters():
    return get_legacy_datacenters()


@router.get("/applications")
async def list_applications():
    return get_applications()


@router.get("/environments")
async def list_environments():
    return get_environments()


@router.get("/chg-requests")
async def list_chg_requests():
    return get_chg_requests()


@router.get("/naming-standards")
async def list_naming_standards():
    return get_naming_standards_info()


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
