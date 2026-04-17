"""Git SaaS API routes.

Exposes configuration, status, manual sync, commit history, and diff
endpoints for the Git SaaS integration.
"""

from typing import Any

from fastapi import APIRouter, Query

from app.services.git_saas import (
    get_config,
    update_config,
    get_status,
    manual_sync,
    get_commit_history,
    get_commit_diff,
    reset_repo,
)

router = APIRouter(prefix="/api/git-saas", tags=["git-saas"])


@router.get("/config")
async def read_config() -> dict[str, Any]:
    """Return the current Git SaaS configuration."""
    return await get_config()


@router.put("/config")
async def write_config(body: dict[str, Any]) -> dict[str, Any]:
    """Update Git SaaS configuration fields."""
    return await update_config(body)


@router.get("/status")
async def read_status() -> dict[str, Any]:
    """Return the current status of the Git SaaS integration."""
    return await get_status()


@router.post("/sync")
async def trigger_sync() -> dict[str, Any]:
    """Force a full sync: copy all data, commit, and push."""
    return await manual_sync()


@router.get("/history")
async def read_history(limit: int = Query(50, ge=1, le=500)) -> list[dict[str, str]]:
    """Return recent git commit history."""
    return await get_commit_history(limit)


@router.get("/diff/{sha}")
async def read_diff(sha: str) -> dict[str, str]:
    """Return the diff for a specific commit."""
    diff = await get_commit_diff(sha)
    return {"sha": sha, "diff": diff}


@router.post("/reset")
async def trigger_reset() -> dict[str, Any]:
    """Delete the git repo and reset config. Use with caution."""
    return await reset_repo()
