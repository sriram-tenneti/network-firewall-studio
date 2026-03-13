"""MongoDB connection and initialization for Network Firewall Studio.

Uses motor (async MongoDB driver) for non-blocking database operations.
Connection string is configurable via MONGODB_URI environment variable.
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("MONGODB_DATABASE", "firewall_studio")

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGODB_URI)
    return _client


def get_db() -> AsyncIOMotorDatabase:
    global _db
    if _db is None:
        _db = get_client()[DATABASE_NAME]
    return _db


async def close_connection() -> None:
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None


# Collection names as constants for consistency
COLLECTIONS = {
    "neighbourhoods": "neighbourhoods",
    "security_zones": "security_zones",
    "ngdc_datacenters": "ngdc_datacenters",
    "legacy_datacenters": "legacy_datacenters",
    "applications": "applications",
    "environments": "environments",
    "predefined_destinations": "predefined_destinations",
    "naming_standards": "naming_standards",
    "firewall_rules": "firewall_rules",
    "rule_history": "rule_history",
    "migrations": "migrations",
    "migration_mappings": "migration_mappings",
    "migration_rule_lifecycle": "migration_rule_lifecycle",
    "chg_requests": "chg_requests",
    "ip_ranges": "ip_ranges",
    "org_config": "org_config",
    "policy_matrix": "policy_matrix",
}
