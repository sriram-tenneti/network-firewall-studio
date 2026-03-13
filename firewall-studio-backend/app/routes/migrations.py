from fastapi import APIRouter, HTTPException
from app.database import (
    get_all_migrations, get_migration_by_id, create_migration,
    get_migration_mappings, get_migration_rule_lifecycle,
    validate_migration, submit_migration,
)

router = APIRouter(prefix="/api/migrations", tags=["Migrations"])


@router.get("")
async def list_migrations():
    return get_all_migrations()


@router.get("/{migration_id}")
async def get_migration(migration_id: str):
    migration = get_migration_by_id(migration_id)
    if not migration:
        raise HTTPException(status_code=404, detail="Migration not found")
    return migration


@router.post("")
async def create_new_migration(data: dict):
    return create_migration(data)


@router.get("/{migration_id}/mappings")
async def get_mappings(migration_id: str):
    return get_migration_mappings(migration_id)


@router.get("/{migration_id}/rule-lifecycle")
async def get_rule_lifecycle(migration_id: str):
    return get_migration_rule_lifecycle(migration_id)


@router.post("/{migration_id}/validate")
async def validate(migration_id: str):
    return validate_migration(migration_id)


@router.post("/{migration_id}/submit")
async def submit(migration_id: str):
    result = submit_migration(migration_id)
    if not result:
        raise HTTPException(status_code=404, detail="Migration not found")
    return result
