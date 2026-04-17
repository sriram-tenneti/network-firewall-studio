"""Git SaaS Integration Service.

Automatically commits all rule data, history, and metadata to a GitHub repository
whenever changes occur.  This gives full version control, audit trail, and the
ability to diff / roll back any change across all JSON data stores.

Architecture
------------
- A bare-bones local git repo is initialised under ``GIT_REPO_DIR``.
- Every call to ``notify_change(store_name)`` stages the relevant JSON file,
  commits with an auto-generated message, and (if a remote is configured)
  pushes to origin asynchronously.
- Configuration is persisted in ``git_saas_config.json`` inside
  ``SEPARATE_DATA_DIR`` so it survives server restarts.
- All git operations run in a background thread via ``asyncio.to_thread``
  to keep the FastAPI event-loop non-blocking.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.database import (
    SEED_DATA_DIR,
    LIVE_DATA_DIR,
    SEPARATE_DATA_DIR,
    _get_data_dir,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
GIT_REPO_DIR = Path(__file__).parent.parent.parent / "git-saas-repo"

# Config file lives next to other user-data
_CONFIG_PATH = SEPARATE_DATA_DIR / "git_saas_config.json"

# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------
_DEFAULT_CONFIG: dict[str, Any] = {
    "enabled": False,
    "remote_url": "",          # e.g. https://github.com/org/fw-data.git
    "branch": "main",
    "commit_author_name": "Firewall Studio",
    "commit_author_email": "firewall-studio@noreply.local",
    "auto_push": True,         # push to remote after every commit
    "include_seed_data": False, # whether to track seed data dir
    "include_live_data": True,  # whether to track live data dir
    "include_user_data": True,  # whether to track user-data dir
    "last_commit_sha": "",
    "last_push_at": "",
    "last_error": "",
    "total_commits": 0,
}

# In-memory lock so concurrent saves don't race on git operations
_git_lock = asyncio.Lock()


# ====================================================================
# Config helpers
# ====================================================================

def _load_config() -> dict[str, Any]:
    """Load persisted config (or return defaults)."""
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH) as f:
            stored = json.load(f)
        # Merge with defaults so new keys are always present
        merged = {**_DEFAULT_CONFIG, **stored}
        return merged
    return dict(_DEFAULT_CONFIG)


def _save_config(cfg: dict[str, Any]) -> None:
    SEPARATE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(_CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2, default=str)


async def get_config() -> dict[str, Any]:
    return _load_config()


async def update_config(updates: dict[str, Any]) -> dict[str, Any]:
    """Merge *updates* into persisted config and return the result."""
    cfg = _load_config()
    # Only allow known keys to be updated
    allowed = {
        "enabled", "remote_url", "branch", "commit_author_name",
        "commit_author_email", "auto_push", "include_seed_data",
        "include_live_data", "include_user_data",
    }
    for k, v in updates.items():
        if k in allowed:
            cfg[k] = v
    _save_config(cfg)

    # If enabling for the first time, initialise the repo
    if cfg["enabled"]:
        await _ensure_repo()
        if cfg["remote_url"]:
            await _set_remote(cfg["remote_url"])

    return cfg


# ====================================================================
# Low-level git helpers (run in thread pool)
# ====================================================================

def _run_git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run a git command, returning CompletedProcess."""
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"  # never prompt for credentials
    return subprocess.run(
        ["git", *args],
        cwd=cwd or GIT_REPO_DIR,
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )


def _init_repo_sync() -> None:
    """Initialise the git-saas-repo directory if it doesn't exist yet."""
    if (GIT_REPO_DIR / ".git").exists():
        return
    GIT_REPO_DIR.mkdir(parents=True, exist_ok=True)
    _run_git("init")
    cfg = _load_config()
    _run_git("config", "user.name", cfg.get("commit_author_name", "Firewall Studio"))
    _run_git("config", "user.email", cfg.get("commit_author_email", "firewall-studio@noreply.local"))
    # Create initial commit so HEAD exists
    readme = GIT_REPO_DIR / "README.md"
    readme.write_text("# Firewall Studio Data Repository\n\nAuto-managed by Git SaaS integration.\n")
    _run_git("add", "README.md")
    _run_git("commit", "-m", "Initial commit – Firewall Studio Git SaaS")


def _set_remote_sync(url: str) -> None:
    """Set or update the origin remote."""
    result = _run_git("remote", "get-url", "origin")
    if result.returncode == 0:
        _run_git("remote", "set-url", "origin", url)
    else:
        _run_git("remote", "add", "origin", url)


def _copy_data_files_sync() -> list[str]:
    """Copy all tracked data directories into the git repo and return changed file list."""
    cfg = _load_config()
    copied: list[str] = []

    dir_map: list[tuple[str, Path, bool]] = [
        ("data", SEED_DATA_DIR, cfg.get("include_seed_data", False)),
        ("live-data", LIVE_DATA_DIR, cfg.get("include_live_data", True)),
        ("user-data", SEPARATE_DATA_DIR, cfg.get("include_user_data", True)),
    ]

    for folder_name, src_dir, include in dir_map:
        dest = GIT_REPO_DIR / folder_name
        if not include:
            # If previously tracked but now excluded, remove from repo
            if dest.exists():
                shutil.rmtree(dest)
                copied.append(f"{folder_name}/ (removed)")
            continue
        if not src_dir.exists():
            continue
        dest.mkdir(parents=True, exist_ok=True)
        for json_file in sorted(src_dir.glob("*.json")):
            # Skip the git_saas_config itself to avoid circular commits
            if json_file.name == "git_saas_config.json":
                continue
            dst_file = dest / json_file.name
            # Only copy if content differs (avoids unnecessary git changes)
            src_content = json_file.read_bytes()
            if dst_file.exists() and dst_file.read_bytes() == src_content:
                continue
            dst_file.write_bytes(src_content)
            copied.append(f"{folder_name}/{json_file.name}")

    # Also copy the current data-mode's data directory
    active_dir = _get_data_dir()
    if active_dir not in (SEED_DATA_DIR, LIVE_DATA_DIR):
        dest = GIT_REPO_DIR / "active-data"
        dest.mkdir(parents=True, exist_ok=True)
        for json_file in sorted(active_dir.glob("*.json")):
            dst_file = dest / json_file.name
            src_content = json_file.read_bytes()
            if dst_file.exists() and dst_file.read_bytes() == src_content:
                continue
            dst_file.write_bytes(src_content)
            copied.append(f"active-data/{json_file.name}")

    return copied


def _commit_sync(message: str) -> str | None:
    """Stage all changes, commit, and return the SHA (or None if nothing to commit)."""
    _run_git("add", "-A")
    # Check if there's anything to commit
    status = _run_git("status", "--porcelain")
    if not status.stdout.strip():
        return None  # nothing changed

    cfg = _load_config()
    _run_git("config", "user.name", cfg.get("commit_author_name", "Firewall Studio"))
    _run_git("config", "user.email", cfg.get("commit_author_email", "firewall-studio@noreply.local"))

    result = _run_git("commit", "-m", message)
    if result.returncode != 0:
        raise RuntimeError(f"git commit failed: {result.stderr}")

    sha_result = _run_git("rev-parse", "HEAD")
    return sha_result.stdout.strip()


def _push_sync(branch: str = "main") -> str:
    """Push to origin. Returns stdout+stderr."""
    result = _run_git("push", "-u", "origin", branch)
    if result.returncode != 0:
        raise RuntimeError(f"git push failed: {result.stderr}")
    return result.stdout + result.stderr


def _log_sync(limit: int = 50) -> list[dict[str, str]]:
    """Return recent commits as a list of dicts."""
    if not (GIT_REPO_DIR / ".git").exists():
        return []
    result = _run_git("log", f"--max-count={limit}", "--format=%H|%an|%ae|%aI|%s")
    if result.returncode != 0:
        return []
    commits: list[dict[str, str]] = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("|", 4)
        if len(parts) >= 5:
            commits.append({
                "sha": parts[0],
                "author_name": parts[1],
                "author_email": parts[2],
                "date": parts[3],
                "message": parts[4],
            })
    return commits


def _diff_sync(sha: str) -> str:
    """Return the diff for a specific commit."""
    if not (GIT_REPO_DIR / ".git").exists():
        return ""
    result = _run_git("show", "--stat", "--patch", sha)
    return result.stdout if result.returncode == 0 else result.stderr


# ====================================================================
# Async wrappers
# ====================================================================

async def _ensure_repo() -> None:
    await asyncio.to_thread(_init_repo_sync)


async def _set_remote(url: str) -> None:
    await asyncio.to_thread(_set_remote_sync, url)


async def notify_change(store_name: str, action: str = "updated") -> dict[str, Any]:
    """Called after every _save / _save_ref / _save_separate.

    Copies data files into the git repo, commits, and optionally pushes.
    Returns a summary dict (or empty dict if git-saas is disabled).
    """
    cfg = _load_config()
    if not cfg.get("enabled"):
        return {}

    async with _git_lock:
        try:
            await _ensure_repo()

            # Copy data files
            changed = await asyncio.to_thread(_copy_data_files_sync)
            if not changed:
                return {"status": "no_changes"}

            # Commit
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            message = f"auto: {store_name} {action} ({now})\n\nChanged files:\n" + "\n".join(f"  - {f}" for f in changed)
            sha = await asyncio.to_thread(_commit_sync, message)

            if not sha:
                return {"status": "no_changes"}

            cfg["last_commit_sha"] = sha
            cfg["total_commits"] = cfg.get("total_commits", 0) + 1
            cfg["last_error"] = ""

            # Push if configured
            push_result = ""
            if cfg.get("auto_push") and cfg.get("remote_url"):
                try:
                    push_result = await asyncio.to_thread(_push_sync, cfg.get("branch", "main"))
                    cfg["last_push_at"] = now
                except RuntimeError as e:
                    cfg["last_error"] = str(e)
                    push_result = str(e)

            _save_config(cfg)
            return {
                "status": "committed",
                "sha": sha,
                "changed_files": changed,
                "push_result": push_result,
            }
        except Exception as e:
            cfg["last_error"] = str(e)
            _save_config(cfg)
            return {"status": "error", "error": str(e)}


async def manual_sync() -> dict[str, Any]:
    """Force a full sync: copy all data, commit, and push."""
    cfg = _load_config()
    if not cfg.get("enabled"):
        return {"status": "disabled", "message": "Git SaaS is not enabled"}

    async with _git_lock:
        try:
            await _ensure_repo()
            if cfg.get("remote_url"):
                await _set_remote(cfg["remote_url"])

            changed = await asyncio.to_thread(_copy_data_files_sync)
            if not changed:
                return {"status": "no_changes", "message": "All data is already up to date"}

            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            message = f"manual sync ({now})\n\nChanged files:\n" + "\n".join(f"  - {f}" for f in changed)
            sha = await asyncio.to_thread(_commit_sync, message)

            cfg["last_commit_sha"] = sha or cfg.get("last_commit_sha", "")
            cfg["total_commits"] = cfg.get("total_commits", 0) + (1 if sha else 0)

            push_result = ""
            if cfg.get("remote_url"):
                try:
                    push_result = await asyncio.to_thread(_push_sync, cfg.get("branch", "main"))
                    cfg["last_push_at"] = now
                    cfg["last_error"] = ""
                except RuntimeError as e:
                    cfg["last_error"] = str(e)
                    push_result = str(e)

            _save_config(cfg)
            return {
                "status": "synced",
                "sha": sha,
                "changed_files": changed,
                "push_result": push_result,
            }
        except Exception as e:
            cfg["last_error"] = str(e)
            _save_config(cfg)
            return {"status": "error", "error": str(e)}


async def get_commit_history(limit: int = 50) -> list[dict[str, str]]:
    """Return recent git commits."""
    return await asyncio.to_thread(_log_sync, limit)


async def get_commit_diff(sha: str) -> str:
    """Return the diff for a specific commit."""
    return await asyncio.to_thread(_diff_sync, sha)


async def get_status() -> dict[str, Any]:
    """Return the current status of the git-saas integration."""
    cfg = _load_config()
    repo_exists = (GIT_REPO_DIR / ".git").exists()

    # Count files in repo
    file_count = 0
    if repo_exists:
        for ext in ("*.json",):
            file_count += len(list(GIT_REPO_DIR.rglob(ext)))

    return {
        "enabled": cfg.get("enabled", False),
        "repo_initialised": repo_exists,
        "remote_url": cfg.get("remote_url", ""),
        "branch": cfg.get("branch", "main"),
        "auto_push": cfg.get("auto_push", True),
        "last_commit_sha": cfg.get("last_commit_sha", ""),
        "last_push_at": cfg.get("last_push_at", ""),
        "last_error": cfg.get("last_error", ""),
        "total_commits": cfg.get("total_commits", 0),
        "tracked_files": file_count,
        "repo_path": str(GIT_REPO_DIR),
    }


async def reset_repo() -> dict[str, Any]:
    """Delete the git repo and reset config. Used for troubleshooting."""
    if GIT_REPO_DIR.exists():
        shutil.rmtree(GIT_REPO_DIR)
    cfg = _load_config()
    cfg["last_commit_sha"] = ""
    cfg["last_push_at"] = ""
    cfg["last_error"] = ""
    cfg["total_commits"] = 0
    _save_config(cfg)
    return {"status": "reset", "message": "Git SaaS repo has been reset"}
