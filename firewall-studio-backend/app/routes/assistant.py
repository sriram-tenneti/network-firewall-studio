"""
Module Assistant — AI-powered contextual assistant for each module.

Processes natural-language queries, classifies intent, executes actions
via existing API functions, and returns structured responses with
suggestions, metrics, and error diagnostics.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import re
import json as json_lib
from datetime import datetime

from app.database import (
    get_rules, get_legacy_rules, get_groups, get_applications,
    get_neighbourhoods, get_security_zones, get_ngdc_datacenters,
    get_policy_matrix, get_org_config, get_environments,
    get_migration_history, get_rule_modifications,
    get_birthright_matrix, get_chg_requests,
    create_group, create_rule_modification, create_application,
    get_group, add_group_member, remove_group_member,
    migrate_rule_to_ngdc, compile_legacy_rule,
    validate_birthright, get_ngdc_recommendations,
)

router = APIRouter(prefix="/api/assistant", tags=["Module Assistant"])


# --------------- Models ---------------

class AssistantQuery(BaseModel):
    module: str  # design-studio, migration, firewall-management, data-import, settings, review, lifecycle
    query: str
    context: Optional[dict] = None  # current app, env, rule, etc.
    user_role: Optional[str] = "admin"  # admin, reviewer, operator, viewer


class AssistantAction(BaseModel):
    action: str
    params: Optional[dict] = None
    module: str
    context: Optional[dict] = None
    user_role: Optional[str] = "admin"


class AssistantResponse(BaseModel):
    message: str
    intent: str
    actions_taken: list = []
    suggestions: list = []
    data: Optional[dict] = None
    error: Optional[str] = None
    services: list = []


# --------------- Role Permissions ---------------

ROLE_PERMISSIONS = {
    "admin": {"read", "write", "delete", "approve", "deploy", "configure"},
    "reviewer": {"read", "approve", "reject"},
    "operator": {"read", "write", "deploy"},
    "viewer": {"read"},
}

def check_permission(role: str, required: str) -> bool:
    perms = ROLE_PERMISSIONS.get(role, set())
    return required in perms


# --------------- Module Service Catalogs ---------------

MODULE_SERVICES = {
    "design-studio": {
        "name": "Design Studio Assistant",
        "description": "Helps create, modify, and manage NGDC firewall rules in the Design Studio",
        "services": [
            {"id": "create_rule", "name": "Create New Rule", "description": "Create a new NGDC firewall rule with source, destination, and service configuration", "permission": "write", "icon": "plus"},
            {"id": "modify_rule", "name": "Modify Rule", "description": "Modify an existing rule's source, destination, service, or action", "permission": "write", "icon": "edit"},
            {"id": "compile_rule", "name": "Compile Rule", "description": "Compile a rule to vendor-specific device policy (Palo Alto, Fortinet, Cisco, Juniper)", "permission": "read", "icon": "code"},
            {"id": "submit_review", "name": "Submit for Review", "description": "Submit a draft rule for approval in the Review & Approval workflow", "permission": "write", "icon": "send"},
            {"id": "manage_groups", "name": "Manage Groups", "description": "Create, modify, or view firewall groups and their members", "permission": "write", "icon": "layers"},
            {"id": "check_compliance", "name": "Check Compliance", "description": "Validate naming standards, birthright access, and policy compliance", "permission": "read", "icon": "shield"},
            {"id": "view_rules", "name": "View Rules", "description": "List and search rules by app, environment, status, or source/destination", "permission": "read", "icon": "list"},
            {"id": "rule_metrics", "name": "Rule Metrics", "description": "Get rule counts, status distribution, compliance stats for your app", "permission": "read", "icon": "bar-chart"},
            {"id": "diagnose_error", "name": "Diagnose Issues", "description": "Troubleshoot rule creation errors, validation failures, or policy conflicts", "permission": "read", "icon": "alert-triangle"},
            {"id": "explain_concept", "name": "Explain Concepts", "description": "Explain NGDC concepts like neighbourhoods, security zones, birthright, naming standards", "permission": "read", "icon": "book"},
        ]
    },
    "migration": {
        "name": "Migration Studio Assistant",
        "description": "Helps migrate legacy firewall rules to NGDC standards",
        "services": [
            {"id": "migrate_rule", "name": "Migrate Rule", "description": "Migrate a legacy rule to NGDC standards with group mapping and policy validation", "permission": "write", "icon": "arrow-right"},
            {"id": "migration_status", "name": "Migration Status", "description": "Check migration progress for an app — how many rules migrated vs remaining", "permission": "read", "icon": "pie-chart"},
            {"id": "view_recommendations", "name": "View Recommendations", "description": "Get NGDC recommendations for a legacy rule including NH/SZ mapping and group suggestions", "permission": "read", "icon": "lightbulb"},
            {"id": "validate_birthright", "name": "Validate Birthright", "description": "Check if a rule qualifies for birthright (auto-approved) access", "permission": "read", "icon": "check-circle"},
            {"id": "group_mapping", "name": "Group Mapping", "description": "Map legacy groups to NGDC groups with component-level granularity", "permission": "write", "icon": "git-merge"},
            {"id": "compile_migration", "name": "Compile Migration", "description": "Compile a migrated rule to vendor-specific policy for validation", "permission": "read", "icon": "code"},
            {"id": "submit_migration", "name": "Submit Migration", "description": "Submit migrated rule for review and approval", "permission": "write", "icon": "send"},
            {"id": "bulk_migrate", "name": "Bulk Migrate", "description": "Migrate multiple rules at once for an app or environment", "permission": "write", "icon": "layers"},
            {"id": "migration_metrics", "name": "Migration Metrics", "description": "Get migration statistics — completion %, apps in progress, blocked rules", "permission": "read", "icon": "bar-chart"},
            {"id": "diagnose_error", "name": "Diagnose Issues", "description": "Troubleshoot migration failures, mapping conflicts, or compliance blocks", "permission": "read", "icon": "alert-triangle"},
        ]
    },
    "firewall-management": {
        "name": "Firewall Management Assistant",
        "description": "Helps manage imported legacy firewall rules and their modifications",
        "services": [
            {"id": "view_rules", "name": "View Legacy Rules", "description": "List and search imported legacy rules by app, environment, or status", "permission": "read", "icon": "list"},
            {"id": "modify_rule", "name": "Modify Rule", "description": "Modify source, destination, service, or action on a legacy rule", "permission": "write", "icon": "edit"},
            {"id": "compile_rule", "name": "Compile Rule", "description": "Compile a legacy rule to vendor-specific device policy", "permission": "read", "icon": "code"},
            {"id": "manage_groups", "name": "Manage Legacy Groups", "description": "View and manage legacy groups auto-created from imported rules", "permission": "write", "icon": "layers"},
            {"id": "export_rules", "name": "Export Rules", "description": "Export rules to Excel for an app or environment", "permission": "read", "icon": "download"},
            {"id": "check_duplicates", "name": "Check Duplicates", "description": "Find duplicate rules based on source, destination, and service", "permission": "read", "icon": "copy"},
            {"id": "rule_metrics", "name": "Rule Analytics", "description": "Get rule counts by app, standard vs non-standard, environment distribution", "permission": "read", "icon": "bar-chart"},
            {"id": "diagnose_error", "name": "Diagnose Issues", "description": "Troubleshoot rule modification errors or validation failures", "permission": "read", "icon": "alert-triangle"},
        ]
    },
    "data-import": {
        "name": "Data Import Assistant",
        "description": "Helps import firewall rules from Excel/JSON files and manage app onboarding",
        "services": [
            {"id": "import_guidance", "name": "Import Guidance", "description": "Get help with file format, required columns, and import best practices", "permission": "read", "icon": "file-text"},
            {"id": "onboard_app", "name": "Onboard Application", "description": "Step-by-step guidance for onboarding a new application into the system", "permission": "write", "icon": "user-plus"},
            {"id": "import_status", "name": "Import Status", "description": "Check status of recent imports — success counts, duplicates, errors", "permission": "read", "icon": "check-circle"},
            {"id": "manage_apps", "name": "Manage Applications", "description": "Create, update, or view application registrations and DC mappings", "permission": "write", "icon": "grid"},
            {"id": "ip_mappings", "name": "IP Mappings", "description": "Manage legacy-to-NGDC IP address mappings for migration", "permission": "write", "icon": "map"},
            {"id": "diagnose_error", "name": "Diagnose Import Errors", "description": "Troubleshoot import failures, format issues, or validation errors", "permission": "read", "icon": "alert-triangle"},
        ]
    },
    "settings": {
        "name": "Settings Assistant",
        "description": "Helps configure system settings, reference data, and organizational policies",
        "services": [
            {"id": "manage_nh", "name": "Manage Neighbourhoods", "description": "Create, update, or delete neighbourhood registries", "permission": "configure", "icon": "map-pin"},
            {"id": "manage_sz", "name": "Manage Security Zones", "description": "Create, update, or delete security zones", "permission": "configure", "icon": "shield"},
            {"id": "manage_dc", "name": "Manage Data Centers", "description": "Create, update, or delete NGDC and legacy data centers", "permission": "configure", "icon": "server"},
            {"id": "manage_policy", "name": "Manage Policy Matrix", "description": "View and edit the policy matrix for traffic flow decisions", "permission": "configure", "icon": "grid"},
            {"id": "manage_apps", "name": "Manage Applications", "description": "Register applications with DC/NH/SZ/component mappings", "permission": "configure", "icon": "grid"},
            {"id": "naming_standards", "name": "Naming Standards", "description": "View and update naming conventions for groups, servers, and subnets", "permission": "configure", "icon": "tag"},
            {"id": "birthright_matrix", "name": "Birthright Matrix", "description": "Manage auto-approved access patterns for birthright validation", "permission": "configure", "icon": "check-circle"},
            {"id": "explain_config", "name": "Explain Configuration", "description": "Explain what each setting does and how it affects the system", "permission": "read", "icon": "info"},
        ]
    },
    "review": {
        "name": "Review & Approval Assistant",
        "description": "Helps manage the review and approval workflow for rules and modifications",
        "services": [
            {"id": "pending_reviews", "name": "Pending Reviews", "description": "List all pending review requests awaiting approval", "permission": "read", "icon": "clock"},
            {"id": "approve_review", "name": "Approve Review", "description": "Approve a pending rule or modification review", "permission": "approve", "icon": "check"},
            {"id": "reject_review", "name": "Reject Review", "description": "Reject a review with feedback notes", "permission": "approve", "icon": "x"},
            {"id": "review_metrics", "name": "Review Metrics", "description": "Get approval rates, average review time, pending count by module", "permission": "read", "icon": "bar-chart"},
            {"id": "review_history", "name": "Review History", "description": "View past approvals and rejections with reviewer notes", "permission": "read", "icon": "history"},
            {"id": "diagnose_error", "name": "Diagnose Issues", "description": "Troubleshoot review workflow issues or stuck approvals", "permission": "read", "icon": "alert-triangle"},
        ]
    },
    "lifecycle": {
        "name": "Lifecycle Dashboard Assistant",
        "description": "Helps track and manage rule lifecycle states and transitions",
        "services": [
            {"id": "lifecycle_summary", "name": "Lifecycle Summary", "description": "Get overview of rules across all lifecycle states", "permission": "read", "icon": "activity"},
            {"id": "transition_rule", "name": "Transition Rule", "description": "Move a rule to its next lifecycle state (e.g., Draft → Submitted → Approved → Deployed)", "permission": "write", "icon": "arrow-right"},
            {"id": "lifecycle_metrics", "name": "Lifecycle Metrics", "description": "Get distribution of rules by state, average time in each state", "permission": "read", "icon": "bar-chart"},
            {"id": "app_lifecycle", "name": "App Lifecycle Status", "description": "Check migration lifecycle status for a specific application", "permission": "read", "icon": "git-branch"},
            {"id": "diagnose_error", "name": "Diagnose Issues", "description": "Troubleshoot lifecycle transition errors or blocked states", "permission": "read", "icon": "alert-triangle"},
        ]
    },
}


# --------------- Intent Classification ---------------

INTENT_PATTERNS = {
    # Greetings
    "greeting": [r"\b(hi|hello|hey|good morning|good afternoon|howdy|greetings)\b"],
    # Counts / Metrics
    "count_rules": [r"\bhow many rules\b", r"\brule count\b", r"\btotal rules\b", r"\bnumber of rules\b"],
    "count_groups": [r"\bhow many groups\b", r"\bgroup count\b", r"\btotal groups\b"],
    "count_apps": [r"\bhow many app\b", r"\bapp count\b", r"\btotal app\b"],
    "metrics": [r"\bmetrics\b", r"\bstatistics\b", r"\bstats\b", r"\banalytics\b", r"\bdashboard\b", r"\breport\b", r"\bsummary\b"],
    # CRUD
    "create_rule": [r"\bcreate.*(rule|firewall)\b", r"\badd.*(rule|new rule)\b", r"\bnew rule\b"],
    "modify_rule": [r"\bmodify rule\b", r"\bedit rule\b", r"\bchange rule\b", r"\bupdate rule\b"],
    "delete_rule": [r"\bdelete rule\b", r"\bremove rule\b"],
    "create_group": [r"\bcreate.*group\b", r"\badd.*group\b", r"\bnew group\b"],
    "modify_group": [r"\bmodify.*group\b", r"\bedit.*group\b", r"\bupdate.*group\b", r"\badd.*member\b", r"\bremove.*member\b"],
    # View / Search
    "view_rules": [r"\blist rules\b", r"\bshow rules\b", r"\bview rules\b", r"\bfind rules\b", r"\bsearch rules\b", r"\bget rules\b"],
    "view_groups": [r"\blist groups\b", r"\bshow groups\b", r"\bview groups\b", r"\bfind groups\b"],
    "view_apps": [r"\blist apps\b", r"\bshow apps\b", r"\bview apps\b", r"\bapplications\b"],
    # Migration
    "migrate": [r"\bmigrate\b", r"\bmigration\b", r"\bconvert.*ngdc\b"],
    "migration_status": [r"\bmigration status\b", r"\bmigration progress\b", r"\bhow.*migrat\b"],
    # Compile
    "compile": [r"\bcompile\b", r"\bgenerate policy\b", r"\bdevice policy\b", r"\bvendor config\b"],
    # Review
    "submit_review": [r"\bsubmit.*review\b", r"\bsend.*approval\b", r"\brequest.*approval\b"],
    "approve": [r"\bapprove\b", r"\baccept\b"],
    "reject": [r"\breject\b", r"\bdeny\b", r"\bdecline\b"],
    "pending_reviews": [r"\bpending\b.*review\b", r"\bawaiting.*approval\b", r"\bwhat.*review\b"],
    # Compliance
    "compliance": [r"\bcomplian\b", r"\bvalidat\b", r"\bstandard\b", r"\bnaming\b"],
    "birthright": [r"\bbirthright\b", r"\bauto.?approv\b"],
    # Configuration
    "config": [r"\bconfig\b", r"\bsetting\b", r"\bconfigure\b"],
    "neighbourhood": [r"\bneighbourhood\b", r"\bnh\b"],
    "security_zone": [r"\bsecurity zone\b", r"\bsz\b"],
    "datacenter": [r"\bdata.?cent\b", r"\bdc\b"],
    # Import
    "import": [r"\bimport\b", r"\bupload\b", r"\bonboard\b"],
    # Explain / Help
    "explain": [r"\bexplain\b", r"\bwhat is\b", r"\bwhat are\b", r"\bhow does\b", r"\btell me about\b", r"\bhelp\b", r"\bwhat can you\b"],
    # Error diagnosis
    "diagnose": [r"\berror\b", r"\bfail\b", r"\bwhy.*not\b", r"\bdoesn.?t work\b", r"\bbroke\b", r"\bissue\b", r"\bproblem\b", r"\btroubleshoot\b", r"\bdiagnos\b"],
    # Lifecycle
    "lifecycle": [r"\blifecycle\b", r"\bstate\b", r"\btransition\b"],
    # Export
    "export": [r"\bexport\b", r"\bdownload\b"],
    # Policy
    "policy_matrix": [r"\bpolicy matrix\b", r"\bpolicy\b", r"\btraffic flow\b"],
}


def classify_intent(query: str) -> str:
    q = query.lower().strip()
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, q):
                return intent
    return "general"


# --------------- Concept Explanations ---------------

CONCEPTS = {
    "neighbourhood": "A Neighbourhood (NH) is a logical grouping of network zones within a data center. It represents a trust boundary — traffic between neighbourhoods typically requires firewall rules. Examples: NH-PROD, NH-DMZ, NH-MGMT.",
    "security_zone": "A Security Zone (SZ) is a segment within a neighbourhood that groups servers/services with similar security postures. Traffic between security zones may or may not be permitted based on the policy matrix. Examples: SZ-WEB, SZ-APP, SZ-DB.",
    "ngdc": "NGDC (Next-Generation Data Center) is the target architecture for firewall rule migration. NGDC enforces standardized naming (grp-{APP}-{NH}-{SZ}-{Component}), structured group management, and policy-driven access control.",
    "birthright": "Birthright access is a set of pre-approved network access patterns that don't require individual review. If a rule matches the birthright matrix (matching source NH/SZ to destination NH/SZ with approved services), it's auto-approved.",
    "naming_standards": "NGDC naming standards require specific prefixes: grp- for groups, svr- for servers, rng- for ranges, sub- for subnets. Full group naming: grp-{APP}-{NH}-{SZ}-{Component}. Legacy groups use various prefixes like g-, ggrp-, netgrp-, etc.",
    "policy_matrix": "The Policy Matrix defines which traffic flows are Permitted, Blocked, or Need Exception between source and destination NH/SZ combinations. It's the foundation for rule validation — every rule must be checked against the matrix.",
    "legacy_group": "Legacy Groups are firewall groups imported from existing rules. They use non-standard naming (g-, ggrp-, gapigr-, etc.) and are visible in Firewall Management for backward compatibility. They can be mapped to NGDC groups during migration.",
    "ngdc_group": "NGDC Groups follow the naming standard grp-{APP}-{NH}-{SZ}-{Component}. They are the target format for all groups in the new architecture and are managed through the App Groups (Manage Groups) interface.",
    "rule_lifecycle": "Rules follow a lifecycle: Draft → Submitted → In Progress → Approved/Rejected → Deployed. Each transition requires specific permissions. Modifications create new versions tracked with delta comparisons.",
    "migration": "Migration converts legacy firewall rules to NGDC standards. It involves: 1) Analyzing the legacy rule, 2) Mapping to NH/SZ, 3) Creating NGDC groups, 4) Validating against policy matrix, 5) Compiling to device policy, 6) Submitting for review.",
    "compile": "Rule compilation translates a firewall rule into vendor-specific device configuration. Supported vendors: Palo Alto (PAN-OS), Fortinet (FortiGate), Cisco ASA, Juniper SRX, and a generic format.",
    "review_approval": "Review & Approval is the governance workflow. Rule changes, group modifications, and migrations must be submitted for review. Reviewers can approve or reject with notes. Approved changes can then be deployed.",
    "data_center": "Data Centers are physical or logical locations where applications are hosted. NGDC data centers follow the new architecture. Legacy data centers are from the old infrastructure being migrated.",
    "group_policy": "When a group's members change (add/remove IPs, subnets, ranges), all rules referencing that group are affected. Group changes must go through Review & Approval and be deployed alongside the rules.",
}


# --------------- Query Processing ---------------

async def process_query(module: str, query: str, context: dict, user_role: str) -> AssistantResponse:
    intent = classify_intent(query)
    q_lower = query.lower()

    # Always include module services in response
    module_info = MODULE_SERVICES.get(module, MODULE_SERVICES.get("design-studio"))
    available_services = [
        s for s in module_info["services"]
        if check_permission(user_role, s["permission"])
    ]

    # --- Greeting ---
    if intent == "greeting":
        return AssistantResponse(
            message=f"Hello! I'm the {module_info['name']}. {module_info['description']}. How can I help you today?",
            intent=intent,
            suggestions=["What services can you provide?", "Show me rule metrics", "Help me create a new rule"],
            services=available_services,
        )

    # --- Service catalog ---
    if intent == "explain" and ("what can you" in q_lower or "services" in q_lower or "help" in q_lower and "what" in q_lower):
        svc_list = "\n".join([f"• **{s['name']}**: {s['description']}" for s in available_services])
        return AssistantResponse(
            message=f"I'm the {module_info['name']}. Here's what I can do for you:\n\n{svc_list}",
            intent="service_catalog",
            services=available_services,
        )

    # --- Explain concepts ---
    if intent == "explain":
        for concept_key, explanation in CONCEPTS.items():
            if concept_key.replace("_", " ") in q_lower or concept_key.replace("_", "") in q_lower:
                return AssistantResponse(
                    message=explanation,
                    intent=intent,
                    suggestions=[f"How do I manage {concept_key.replace('_', ' ')}s?", "Show me related metrics"],
                )
        return AssistantResponse(
            message="I can explain NGDC concepts like neighbourhoods, security zones, birthright access, naming standards, policy matrix, groups, migration, compilation, and more. What would you like to know about?",
            intent=intent,
            suggestions=list(CONCEPTS.keys())[:8],
        )

    # --- Metrics / Reports ---
    if intent in ("metrics", "count_rules", "count_groups", "count_apps", "rule_metrics"):
        try:
            rules = await get_rules()
            legacy_rules = await get_legacy_rules()
            groups = await get_groups()
            apps = await get_applications()

            # Compute metrics
            total_rules = len(rules)
            total_legacy = len(legacy_rules)
            total_groups = len(groups)
            total_apps = len(apps)

            # Status distribution
            status_dist = {}
            for r in rules:
                st = r.get("status", "Unknown")
                status_dist[st] = status_dist.get(st, 0) + 1

            # Legacy standard vs non-standard
            standard_count = sum(1 for r in legacy_rules if r.get("is_standard"))
            non_standard = total_legacy - standard_count

            # App-wise rule counts
            app_rules = {}
            for r in legacy_rules:
                aid = r.get("app_distributed_id") or str(r.get("app_id", ""))
                app_rules[aid] = app_rules.get(aid, 0) + 1

            # Group classification
            ngdc_groups = sum(1 for g in groups if re.match(r"^grp-[A-Za-z0-9]+-[A-Za-z0-9]+-[A-Za-z0-9]+-[A-Za-z0-9]+", g.get("name", "")))
            legacy_groups_count = total_groups - ngdc_groups

            # Migration status
            migrated = sum(1 for r in legacy_rules if r.get("migration_status") == "Migrated")

            data = {
                "studio_rules": total_rules,
                "legacy_rules": total_legacy,
                "groups": total_groups,
                "applications": total_apps,
                "status_distribution": status_dist,
                "standard_rules": standard_count,
                "non_standard_rules": non_standard,
                "ngdc_groups": ngdc_groups,
                "legacy_groups": legacy_groups_count,
                "migrated_rules": migrated,
                "not_migrated": total_legacy - migrated,
                "top_apps": dict(sorted(app_rules.items(), key=lambda x: x[1], reverse=True)[:10]),
            }

            msg_lines = [
                f"📊 **System Metrics Overview**",
                f"",
                f"**Rules:** {total_rules} Studio | {total_legacy} Legacy ({standard_count} standard, {non_standard} non-standard)",
                f"**Groups:** {total_groups} total ({ngdc_groups} NGDC, {legacy_groups_count} Legacy)",
                f"**Applications:** {total_apps} registered",
                f"**Migration:** {migrated}/{total_legacy} rules migrated ({round(migrated/max(total_legacy,1)*100)}%)",
            ]
            if status_dist:
                msg_lines.append(f"**Status Distribution:** {', '.join(f'{k}: {v}' for k, v in status_dist.items())}")
            if app_rules:
                top3 = list(sorted(app_rules.items(), key=lambda x: x[1], reverse=True))[:3]
                msg_lines.append(f"**Top Apps:** {', '.join(f'{a}: {c} rules' for a, c in top3)}")

            return AssistantResponse(
                message="\n".join(msg_lines),
                intent=intent,
                data=data,
                suggestions=["Show me migration progress", "List non-standard rules", "Show group details"],
            )
        except Exception as e:
            return AssistantResponse(
                message=f"I encountered an error fetching metrics: {str(e)}",
                intent=intent,
                error=str(e),
            )

    # --- View Rules ---
    if intent == "view_rules":
        try:
            app_id = context.get("app_id") if context else None
            if module == "firewall-management":
                rules = await get_legacy_rules(app_id=app_id)
                count = len(rules)
                sample = rules[:5]
                return AssistantResponse(
                    message=f"Found **{count}** legacy rules{f' for app {app_id}' if app_id else ''}. Showing first {min(5, count)}:",
                    intent=intent,
                    data={"total": count, "rules": [{"id": r.get("id"), "app_id": r.get("app_id"), "source": r.get("rule_source", "")[:50], "destination": r.get("rule_destination", "")[:50], "action": r.get("rule_action")} for r in sample]},
                    suggestions=["Show rules for a specific app", "Show non-standard rules", "Export rules"],
                )
            else:
                rules = await get_rules()
                count = len(rules)
                sample = rules[:5]
                return AssistantResponse(
                    message=f"Found **{count}** studio rules. Showing first {min(5, count)}:",
                    intent=intent,
                    data={"total": count, "rules": [{"id": r.get("id"), "app": r.get("application"), "status": r.get("status"), "source": str(r.get("source", {}))} for r in sample]},
                    suggestions=["Filter by app", "Filter by status", "Show rule details"],
                )
        except Exception as e:
            return AssistantResponse(message=f"Error fetching rules: {str(e)}", intent=intent, error=str(e))

    # --- View Groups ---
    if intent in ("view_groups", "count_groups"):
        try:
            app_id = context.get("app_id") if context else None
            groups = await get_groups(app_id=app_id)
            count = len(groups)
            ngdc_pattern = re.compile(r"^grp-[A-Za-z0-9]+-[A-Za-z0-9]+-[A-Za-z0-9]+-[A-Za-z0-9]+")
            ngdc = [g for g in groups if ngdc_pattern.match(g.get("name", ""))]
            legacy = [g for g in groups if not ngdc_pattern.match(g.get("name", ""))]

            return AssistantResponse(
                message=f"Found **{count}** groups{f' for app {app_id}' if app_id else ''}: **{len(ngdc)}** NGDC, **{len(legacy)}** Legacy.\n\n"
                        + "\n".join([f"• {g['name']} ({len(g.get('members', []))} members)" for g in groups[:10]]),
                intent=intent,
                data={"total": count, "ngdc_count": len(ngdc), "legacy_count": len(legacy),
                       "groups": [{"name": g["name"], "members": len(g.get("members", [])), "type": "NGDC" if ngdc_pattern.match(g.get("name", "")) else "Legacy"} for g in groups[:20]]},
                suggestions=["Show group members", "Create new group", "Show NGDC groups only"],
            )
        except Exception as e:
            return AssistantResponse(message=f"Error fetching groups: {str(e)}", intent=intent, error=str(e))

    # --- View Apps ---
    if intent in ("view_apps", "count_apps"):
        try:
            apps = await get_applications()
            count = len(apps)
            return AssistantResponse(
                message=f"Found **{count}** registered applications:\n\n" + "\n".join([f"• {a.get('app_distributed_id', a.get('app_id'))} — {a.get('app_name', 'N/A')}" for a in apps[:15]]),
                intent=intent,
                data={"total": count, "applications": [{"id": a.get("app_distributed_id", a.get("app_id")), "name": a.get("app_name"), "environment": a.get("environment")} for a in apps[:20]]},
                suggestions=["Show app details", "Onboard new app", "Show app migration status"],
            )
        except Exception as e:
            return AssistantResponse(message=f"Error fetching applications: {str(e)}", intent=intent, error=str(e))

    # --- Migration status ---
    if intent in ("migration_status", "migrate"):
        try:
            legacy_rules = await get_legacy_rules()
            migrated = [r for r in legacy_rules if r.get("migration_status") == "Migrated"]
            not_migrated = [r for r in legacy_rules if r.get("migration_status") != "Migrated"]

            # Per-app breakdown
            app_migration = {}
            for r in legacy_rules:
                aid = r.get("app_distributed_id") or str(r.get("app_id", ""))
                if aid not in app_migration:
                    app_migration[aid] = {"total": 0, "migrated": 0}
                app_migration[aid]["total"] += 1
                if r.get("migration_status") == "Migrated":
                    app_migration[aid]["migrated"] += 1

            msg = f"**Migration Progress:**\n\n"
            msg += f"• **{len(migrated)}** / **{len(legacy_rules)}** rules migrated ({round(len(migrated)/max(len(legacy_rules),1)*100)}%)\n"
            msg += f"• **{len(not_migrated)}** rules remaining\n\n"

            if app_migration:
                msg += "**Per-App Breakdown:**\n"
                for aid, info in sorted(app_migration.items(), key=lambda x: x[1]["total"], reverse=True)[:10]:
                    pct = round(info["migrated"] / max(info["total"], 1) * 100)
                    msg += f"• {aid}: {info['migrated']}/{info['total']} ({pct}%)\n"

            return AssistantResponse(
                message=msg,
                intent=intent,
                data={"total": len(legacy_rules), "migrated": len(migrated), "remaining": len(not_migrated), "per_app": app_migration},
                suggestions=["Migrate rules for an app", "Show blocked rules", "View migration history"],
            )
        except Exception as e:
            return AssistantResponse(message=f"Error checking migration status: {str(e)}", intent=intent, error=str(e))

    # --- Pending Reviews ---
    if intent == "pending_reviews":
        try:
            mods = await get_rule_modifications()
            pending = [m for m in mods if m.get("status") == "pending"]
            approved = [m for m in mods if m.get("status") == "approved"]
            rejected = [m for m in mods if m.get("status") == "rejected"]

            return AssistantResponse(
                message=f"**Review Queue:**\n\n• **{len(pending)}** pending reviews\n• **{len(approved)}** approved\n• **{len(rejected)}** rejected\n\n"
                        + ("\n".join([f"• [{m.get('id', '')[:8]}] Rule {m.get('rule_id')} — {m.get('comments', 'No comments')[:60]}" for m in pending[:10]]) if pending else "No pending reviews!"),
                intent=intent,
                data={"pending": len(pending), "approved": len(approved), "rejected": len(rejected), "reviews": [{"id": m.get("id"), "rule_id": m.get("rule_id"), "status": m.get("status"), "comments": m.get("comments")} for m in pending[:10]]},
                suggestions=["Approve all pending", "Show review details", "Show review history"],
            )
        except Exception as e:
            return AssistantResponse(message=f"Error fetching reviews: {str(e)}", intent=intent, error=str(e))

    # --- Compliance / Naming ---
    if intent == "compliance":
        try:
            rules = await get_legacy_rules()
            standard = sum(1 for r in rules if r.get("is_standard"))
            non_standard = len(rules) - standard
            return AssistantResponse(
                message=f"**Compliance Summary:**\n\n• **{standard}** rules meet naming standards\n• **{non_standard}** rules need attention\n• Compliance rate: **{round(standard/max(len(rules),1)*100)}%**\n\nNon-standard rules typically have naming issues in source/destination that don't follow grp-/svr-/rng- conventions.",
                intent=intent,
                data={"standard": standard, "non_standard": non_standard, "total": len(rules), "compliance_pct": round(standard / max(len(rules), 1) * 100)},
                suggestions=["Show non-standard rules", "Explain naming standards", "Fix naming issues"],
            )
        except Exception as e:
            return AssistantResponse(message=f"Error checking compliance: {str(e)}", intent=intent, error=str(e))

    # --- Birthright ---
    if intent == "birthright":
        try:
            matrix = await get_birthright_matrix()
            entries = matrix.get("production", []) + matrix.get("non_production", [])
            return AssistantResponse(
                message=f"**Birthright Matrix:** {len(entries)} auto-approval patterns configured.\n\nBirthright access allows certain source→destination flows to be auto-approved without manual review. This is based on predefined trust patterns between neighbourhoods and security zones.",
                intent=intent,
                data={"total_entries": len(entries), "production": len(matrix.get("production", [])), "non_production": len(matrix.get("non_production", []))},
                suggestions=["Validate a rule against birthright", "Add birthright entry", "Show birthright details"],
            )
        except Exception as e:
            return AssistantResponse(message=f"Error fetching birthright matrix: {str(e)}", intent=intent, error=str(e))

    # --- Policy Matrix ---
    if intent == "policy_matrix":
        try:
            matrix = await get_policy_matrix()
            return AssistantResponse(
                message=f"**Policy Matrix:** {len(matrix)} entries define traffic flow decisions between NH/SZ combinations.\n\nEach entry specifies whether traffic is Permitted, Blocked, or needs an Exception between a source and destination neighbourhood/security zone pair.",
                intent=intent,
                data={"total_entries": len(matrix), "sample": matrix[:5]},
                suggestions=["Show permitted flows", "Show blocked flows", "Explain policy matrix"],
            )
        except Exception as e:
            return AssistantResponse(message=f"Error fetching policy matrix: {str(e)}", intent=intent, error=str(e))

    # --- Configuration ---
    if intent in ("config", "neighbourhood", "security_zone", "datacenter"):
        try:
            nhs = await get_neighbourhoods()
            szs = await get_security_zones()
            dcs = await get_ngdc_datacenters()
            envs = await get_environments()
            return AssistantResponse(
                message=f"**System Configuration:**\n\n• **{len(nhs)}** Neighbourhoods\n• **{len(szs)}** Security Zones\n• **{len(dcs)}** Data Centers\n• **{len(envs)}** Environments\n\nYou can manage these in the Settings page.",
                intent=intent,
                data={"neighbourhoods": len(nhs), "security_zones": len(szs), "datacenters": len(dcs), "environments": len(envs),
                       "nh_list": [n.get("name") or n.get("nh_id") for n in nhs[:10]],
                       "sz_list": [s.get("name") or s.get("sz_id") for s in szs[:10]],
                       "dc_list": [d.get("name") or d.get("dc_id") for d in dcs[:10]]},
                suggestions=["Show neighbourhood details", "Create neighbourhood", "Show security zones"],
            )
        except Exception as e:
            return AssistantResponse(message=f"Error fetching configuration: {str(e)}", intent=intent, error=str(e))

    # --- Import guidance ---
    if intent == "import":
        return AssistantResponse(
            message="**Data Import Guide:**\n\n"
                    "1. **Excel Import (.xlsx/.xls):** Upload firewall rule exports with columns like Source, Destination, Service, Action, Policy Name, etc.\n"
                    "2. **JSON Import:** Upload structured JSON with rule objects.\n"
                    "3. **App Management Import:** Upload app registrations with DC/NH/SZ mappings.\n"
                    "4. **IP Mapping Import:** Upload legacy-to-NGDC IP address mappings.\n\n"
                    "**Tips:**\n"
                    "• Headers are matched flexibly — common column names are auto-detected\n"
                    "• Duplicate rules are automatically skipped\n"
                    "• Select the target environment before importing\n"
                    "• Large files (50K+ rows) are supported with streaming import",
            intent=intent,
            suggestions=["What columns are required?", "Import Excel file", "Import JSON file", "Check import status"],
        )

    # --- Diagnose errors ---
    if intent == "diagnose":
        diag_tips = []
        if "group" in q_lower:
            diag_tips = [
                "• Group name must follow NGDC standard: grp-{APP}-{NH}-{SZ}-{Component}",
                "• Duplicate group names are rejected — check if group already exists",
                "• Group members must be valid IPs, subnets (CIDR), or ranges",
                "• Empty groups are allowed but will show warnings",
            ]
        elif "import" in q_lower:
            diag_tips = [
                "• Check file format: .xlsx, .xls, or .json are supported",
                "• Verify column headers match expected names (Source, Destination, Service, Action)",
                "• Large files may timeout — check if the import partially succeeded",
                "• HTML-table format Excel files are auto-detected and parsed",
            ]
        elif "migration" in q_lower or "migrate" in q_lower:
            diag_tips = [
                "• Ensure app has DC/NH/SZ mappings configured before migration",
                "• Check if rule source/destination can be mapped to NGDC groups",
                "• Verify policy matrix permits the traffic flow",
                "• Birthright validation must pass or exception must be approved",
            ]
        elif "rule" in q_lower:
            diag_tips = [
                "• Check naming standards: source must start with grp-/svr-/rng-",
                "• Verify destination group exists (create in App Groups first)",
                "• Ensure policy matrix permits the source→destination flow",
                "• Duplicate rules (same source/dest/service) are flagged",
            ]
        elif "review" in q_lower or "approv" in q_lower:
            diag_tips = [
                "• Only users with 'reviewer' or 'admin' role can approve",
                "• Reviews must be in 'pending' status to be approved/rejected",
                "• Group policy changes create separate review entries",
                "• Check if the modification has a valid delta (changes detected)",
            ]
        else:
            diag_tips = [
                "• Check browser console for JavaScript errors",
                "• Verify backend API is running (check /healthz endpoint)",
                "• Look for validation error messages in the UI",
                "• Check network tab for failed API calls",
            ]

        return AssistantResponse(
            message=f"**Troubleshooting Guide:**\n\n" + "\n".join(diag_tips),
            intent=intent,
            suggestions=["Show me the error details", "Check system health", "View recent errors"],
        )

    # --- Export ---
    if intent == "export":
        return AssistantResponse(
            message="**Export Options:**\n\n"
                    "• **Excel Export:** Export legacy rules to .xlsx by app or all rules\n"
                    "• **JSON Seed Export:** Export entire reference data configuration\n"
                    "• **Multi-App Export:** Select multiple apps and export combined\n\n"
                    "Use the Export button in Firewall Management or the Data Admin panel.",
            intent=intent,
            suggestions=["Export rules for an app", "Export all rules", "Export seed data"],
        )

    # --- Lifecycle ---
    if intent == "lifecycle":
        return AssistantResponse(
            message="**Rule Lifecycle States:**\n\n"
                    "1. **Draft** — Rule created, not yet submitted\n"
                    "2. **Submitted** — Sent for review\n"
                    "3. **In Progress** — Under review\n"
                    "4. **Approved** — Passed review, ready for deployment\n"
                    "5. **Rejected** — Review failed, needs modification\n"
                    "6. **Deployed** — Live on firewall devices\n"
                    "7. **Certified** — Compliance-verified\n"
                    "8. **Expired** — Past expiry date\n\n"
                    "Rules can only transition to valid next states. Use the Lifecycle Dashboard to track all rules.",
            intent=intent,
            suggestions=["Show lifecycle summary", "Transition a rule", "Show rules by state"],
        )

    # --- Create group via assistant ---
    if intent == "create_group":
        if not check_permission(user_role, "write"):
            return AssistantResponse(
                message="You don't have permission to create groups. Contact an admin to get write access.",
                intent=intent,
                error="insufficient_permissions",
            )
        return AssistantResponse(
            message="To create a new group, I need:\n\n"
                    "1. **Application** — Which app is this group for?\n"
                    "2. **Neighbourhood (NH)** — Which NH?\n"
                    "3. **Security Zone (SZ)** — Which SZ?\n"
                    "4. **Component** — What component (e.g., web, app, db)?\n"
                    "5. **Members** — IP addresses, subnets, or ranges to include\n\n"
                    "The group name will be auto-generated as: `grp-{APP}-{NH}-{SZ}-{Component}`\n\n"
                    "You can also create groups using the **Manage Groups** button in the Studio.",
            intent=intent,
            suggestions=["Show existing groups", "Create group for APP-001", "Explain group naming"],
        )

    # --- Create rule guidance ---
    if intent == "create_rule":
        if not check_permission(user_role, "write"):
            return AssistantResponse(
                message="You don't have permission to create rules. Contact an admin to get write access.",
                intent=intent,
                error="insufficient_permissions",
            )
        return AssistantResponse(
            message="To create a new NGDC firewall rule, you'll need:\n\n"
                    "1. **Application** — Select the target application\n"
                    "2. **Environment** — Production, Pre-Production, or Non-Production\n"
                    "3. **Source** — IP, subnet, range, or group (with proper prefix)\n"
                    "4. **Source NH/SZ** — Neighbourhood and Security Zone for source\n"
                    "5. **Destination** — Select from available NGDC groups for the app\n"
                    "6. **Destination NH/SZ** — Neighbourhood and Security Zone for destination\n"
                    "7. **Service/Ports** — Service name or port numbers\n"
                    "8. **Action** — Accept or Deny\n\n"
                    "Use the **Create Rule** button in the Design Studio to start.",
            intent=intent,
            suggestions=["Show available apps", "Show NGDC groups for an app", "Explain naming standards"],
        )

    # --- Compile guidance ---
    if intent == "compile":
        return AssistantResponse(
            message="**Rule Compilation** translates rules into vendor-specific device policy:\n\n"
                    "**Supported Vendors:**\n"
                    "• **Palo Alto (PAN-OS)** — XML-based security policy\n"
                    "• **Fortinet (FortiGate)** — CLI-based policy configuration\n"
                    "• **Cisco ASA** — Access-list format\n"
                    "• **Juniper SRX** — Security policy format\n"
                    "• **Generic** — Human-readable summary\n\n"
                    "Select a rule and click **Compile** to generate the device policy.",
            intent=intent,
            suggestions=["Compile a specific rule", "Show compiled policy", "Compare vendor outputs"],
        )

    # --- Default / General ---
    return AssistantResponse(
        message=f"I understand you're asking about: \"{query}\"\n\nI'm the {module_info['name']} and I can help with many tasks. Here are some things you can ask me:",
        intent="general",
        suggestions=[
            "What services can you provide?",
            "Show me metrics and reports",
            "Help me with an error",
            "Explain a concept",
        ],
        services=available_services,
    )


# --------------- Action Execution ---------------

async def execute_action(action: str, params: dict, module: str, context: dict, user_role: str) -> AssistantResponse:
    """Execute a specific action via backend APIs."""

    if not check_permission(user_role, "write") and action in ("create_group", "create_rule", "modify_rule", "migrate_rule"):
        return AssistantResponse(
            message="Insufficient permissions for this action.",
            intent=action,
            error="insufficient_permissions",
        )

    if action == "get_metrics":
        return await process_query(module, "show me metrics", context, user_role)

    if action == "get_groups":
        app_id = params.get("app_id") if params else None
        try:
            groups = await get_groups(app_id=app_id)
            return AssistantResponse(
                message=f"Found {len(groups)} groups",
                intent=action,
                data={"groups": [{"name": g["name"], "members": len(g.get("members", []))} for g in groups]},
            )
        except Exception as e:
            return AssistantResponse(message=f"Error: {str(e)}", intent=action, error=str(e))

    if action == "get_rules":
        try:
            if module == "firewall-management":
                rules = await get_legacy_rules(app_id=params.get("app_id") if params else None)
            else:
                rules = await get_rules()
            return AssistantResponse(
                message=f"Found {len(rules)} rules",
                intent=action,
                data={"rules": [{"id": r.get("id"), "source": str(r.get("rule_source", r.get("source", "")))[:50]} for r in rules[:20]]},
            )
        except Exception as e:
            return AssistantResponse(message=f"Error: {str(e)}", intent=action, error=str(e))

    if action == "create_group" and params:
        try:
            group = await create_group(params)
            return AssistantResponse(
                message=f"Group '{group.get('name')}' created successfully with {len(group.get('members', []))} members!",
                intent=action,
                actions_taken=[f"Created group: {group.get('name')}"],
                data={"group": group},
            )
        except Exception as e:
            return AssistantResponse(message=f"Failed to create group: {str(e)}", intent=action, error=str(e))

    if action == "compile_rule" and params:
        try:
            rule_id = params.get("rule_id")
            vendor = params.get("vendor", "generic")
            compiled = await compile_legacy_rule(rule_id, vendor)
            return AssistantResponse(
                message=f"Rule {rule_id} compiled for {vendor}",
                intent=action,
                actions_taken=[f"Compiled rule {rule_id} for {vendor}"],
                data={"compiled": compiled},
            )
        except Exception as e:
            return AssistantResponse(message=f"Failed to compile: {str(e)}", intent=action, error=str(e))

    return AssistantResponse(
        message=f"Action '{action}' is not yet implemented for execution. Please use the UI to perform this action.",
        intent=action,
        suggestions=["What actions can you perform?", "Show me how to do this manually"],
    )


# --------------- API Endpoints ---------------

@router.post("/query", response_model=AssistantResponse)
async def assistant_query(req: AssistantQuery):
    """Process a natural-language query in the context of a specific module."""
    return await process_query(
        module=req.module,
        query=req.query,
        context=req.context or {},
        user_role=req.user_role or "admin",
    )


@router.post("/action", response_model=AssistantResponse)
async def assistant_action(req: AssistantAction):
    """Execute a specific action via the assistant."""
    return await execute_action(
        action=req.action,
        params=req.params or {},
        module=req.module,
        context=req.context or {},
        user_role=req.user_role or "admin",
    )


@router.get("/services/{module}")
async def get_module_services(module: str, user_role: str = "admin"):
    """Get the list of available services for a module based on user role."""
    module_info = MODULE_SERVICES.get(module)
    if not module_info:
        raise HTTPException(status_code=404, detail=f"Module '{module}' not found. Available: {list(MODULE_SERVICES.keys())}")

    services = [
        s for s in module_info["services"]
        if check_permission(user_role, s["permission"])
    ]

    return {
        "module": module,
        "name": module_info["name"],
        "description": module_info["description"],
        "services": services,
        "user_role": user_role,
    }


@router.get("/modules")
async def list_modules():
    """List all available modules with their assistant capabilities."""
    return [
        {
            "id": module_id,
            "name": info["name"],
            "description": info["description"],
            "service_count": len(info["services"]),
        }
        for module_id, info in MODULE_SERVICES.items()
    ]
