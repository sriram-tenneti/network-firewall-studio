from fastapi import APIRouter, HTTPException
from app.database import (
    get_migrations, get_migration, create_migration,
    get_migration_mappings, create_migration_mapping, execute_migration,
)

router = APIRouter(prefix="/api/migrations", tags=["Migrations"])


@router.get("")
async def list_migrations():
    return await get_migrations()


@router.get("/{migration_id}")
async def get_migration_endpoint(migration_id: str):
    migration = await get_migration(migration_id)
    if not migration:
        raise HTTPException(status_code=404, detail="Migration not found")
    return migration


@router.post("")
async def create_new_migration(data: dict):
    return await create_migration(data)


@router.get("/{migration_id}/mappings")
async def get_mappings(migration_id: str):
    return await get_migration_mappings(migration_id)


@router.post("/{migration_id}/mappings")
async def create_mapping(migration_id: str, data: dict):
    data["migration_id"] = migration_id
    return await create_migration_mapping(data)


@router.get("/{migration_id}/rule-lifecycle")
async def get_rule_lifecycle(migration_id: str):
    mappings = await get_migration_mappings(migration_id)
    return [{"mapping_id": m.get("mapping_id"), "status": m.get("status"),
             "compliance": m.get("compliance"), "legacy_rule": m.get("legacy_rule"),
             "ngdc_source": m.get("ngdc_source"), "ngdc_destination": m.get("ngdc_destination")}
            for m in mappings]


@router.post("/{migration_id}/validate")
async def validate(migration_id: str):
    mappings = await get_migration_mappings(migration_id)
    compliant = sum(1 for m in mappings if m.get("compliance") == "Compliant")
    total = len(mappings)
    return {"migration_id": migration_id, "total": total, "compliant": compliant,
            "non_compliant": total - compliant,
            "compliance_rate": round((compliant / total) * 100, 1) if total > 0 else 0}


@router.post("/{migration_id}/submit")
async def submit(migration_id: str):
    result = await execute_migration(migration_id)
    if not result:
        raise HTTPException(status_code=404, detail="Migration not found")
    return result
