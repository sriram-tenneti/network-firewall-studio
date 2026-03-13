# Network Firewall Studio - Workflow Diagrams

## Document Control

| Property | Value |
|----------|-------|
| **Document Title** | Network Firewall Studio - Workflow Diagrams |
| **Version** | 1.0.0 |
| **Classification** | Internal - Operations |
| **Author** | Network Engineering Team |
| **Last Updated** | 2026-03-13 |
| **Status** | Approved |

---

## Table of Contents

1. [Firewall Rule Creation Workflow](#1-firewall-rule-creation-workflow)
2. [Naming Standards Enforcement Workflow](#2-naming-standards-enforcement-workflow)
3. [Rule Certification Workflow](#3-rule-certification-workflow)
4. [Change Request (CHG) Submission Workflow](#4-change-request-chg-submission-workflow)
5. [Legacy Rule Migration Workflow](#5-legacy-rule-migration-workflow)
6. [NH/SZ Decision Engine Workflow](#6-nhsz-decision-engine-workflow)
7. [Group-to-Group Enforcement Workflow](#7-group-to-group-enforcement-workflow)
8. [Rule Lifecycle State Machine](#8-rule-lifecycle-state-machine)
9. [Drag-and-Drop Destination Workflow](#9-drag-and-drop-destination-workflow)
10. [End-to-End Application Workflow](#10-end-to-end-application-workflow)

---

## 1. Firewall Rule Creation Workflow

### Overview
The primary workflow for creating new firewall rules through the Design Studio interface.

### Workflow Diagram

```
                    START
                      |
                      v
            +-------------------+
            | Select Application|
            | (AppID Lookup)    |
            +--------+----------+
                     |
                     v
            +-------------------+
            | Select            |
            | Neighbourhood     |
            | (NH01 - NH17)     |
            +--------+----------+
                     |
                     v
            +-------------------+
            | Auto-Determine    |
            | Security Zone     |
            | (Decision Engine) |
            +--------+----------+
                     |
                     v
            +-------------------+
            | Build Source Name  |
            | grp-{AppID}-{NH}- |
            | {SZ}-{Subtype}    |
            +--------+----------+
                     |
                     v
            +-------------------+
            | Validate Name     |<--------+
            | (Real-time)       |         |
            +--------+----------+         |
                     |                    |
              +------+------+             |
              |             |             |
          [VALID]      [INVALID]          |
              |             |             |
              v             v             |
     +----------+   +------------+        |
     | Green    |   | Red Alert  |        |
     | Badge    |   | Show Errors+--------+
     | Continue |   +------------+  Fix & Retry
     +----+-----+
          |
          v
    +-------------------+
    | Configure         |
    | Destinations      |
    | (Drag & Drop)     |
    +--------+----------+
             |
             v
    +-------------------+
    | Group-to-Group    |
    | Check             |
    +--------+----------+
             |
      +------+------+
      |             |
   [G2G OK]   [Not G2G]
      |             |
      v             v
+----------+  +------------------+
| Continue |  | Exception        |
|          |  | Required?        |
+----+-----+  +--------+---------+
     |                  |
     |           +------+------+
     |           |             |
     |        [Approve]    [Reject]
     |           |             |
     |           v             v
     |     +-----------+  +---------+
     |     | Mark       |  | Return  |
     |     | Exception  |  | to Edit |
     |     +-----------+  +---------+
     |           |
     +-----+----+
           |
           v
    +-------------------+
    | Select Port /     |
    | Protocol / Action |
    +--------+----------+
             |
             v
    +-------------------+
    | Create Rule       |
    | Status: DRAFT     |
    +--------+----------+
             |
             v
    +-------------------+
    | Add to Rule       |
    | Lifecycle Table   |
    +-------------------+
             |
             v
           END
```

### Workflow Steps

| Step | Action | Actor | System Response |
|------|--------|-------|----------------|
| 1 | Select Application | Network Engineer | Loads AppID, auto-fills NH/SZ if known |
| 2 | Select Neighbourhood | Network Engineer | Displays available NHs with descriptions |
| 3 | Auto-determine SZ | System | Runs decision engine based on app attributes |
| 4 | Build Source Name | System + User | Auto-generates compliant name with user subtype input |
| 5 | Validate Name | System | Real-time validation with green/red indicators |
| 6 | Configure Destinations | Network Engineer | Drag-and-drop interface with available targets |
| 7 | Group-to-Group Check | System | Validates both source and destination are group-based |
| 8 | Select Port/Protocol | Network Engineer | Standard port/protocol/action selection |
| 9 | Create Rule | System | Rule created with DRAFT status |

---

## 2. Naming Standards Enforcement Workflow

### Overview
The naming standards engine enforces strict naming conventions across all firewall objects.

### Workflow Diagram

```
              INPUT NAME
                  |
                  v
         +------------------+
         | Detect Prefix    |
         +--------+---------+
                  |
         +--------+--------+--------+
         |        |        |        |
      [grp-]  [svr-]   [rng-]   [other]
         |        |        |        |
         v        v        v        v
    +--------+ +--------+ +--------+ +--------+
    | Group  | | Server | | Subnet | | INVALID|
    | Valid. | | Valid. | | Valid. | | Prefix |
    +---+----+ +---+----+ +---+----+ +---+----+
        |          |          |          |
        v          v          v          v
  +-----------+-----------+-----------+  ERROR
  |     PARSE NAME SEGMENTS           |
  +-----------------------------------+
  | Segment 1: AppID                  |
  |   - Must exist in registry        |
  |   - Must be uppercase             |
  |                                   |
  | Segment 2: NH (Neighbourhood)     |
  |   - Must be NH01-NH17             |
  |   - Must be valid for app         |
  |                                   |
  | Segment 3: SZ (Security Zone)     |
  |   - Must be valid code            |
  |   - Must align with NH            |
  |                                   |
  | Segment 4: Subtype/Name/Desc      |
  |   - Must be uppercase             |
  |   - Must be alphanumeric          |
  |   - Group: valid subtype list     |
  |   - Server: hostname format       |
  |   - Subnet: descriptor format     |
  +-----------------+-----------------+
                    |
             +------+------+
             |             |
         [ALL VALID]  [HAS ERRORS]
             |             |
             v             v
      +-----------+  +------------------+
      | COMPLIANT |  | NON-COMPLIANT    |
      | Green     |  | Red Badge        |
      | Badge     |  | Error Messages:  |
      |           |  | - Invalid AppID  |
      |           |  | - Invalid NH     |
      |           |  | - Invalid SZ     |
      |           |  | - Invalid format |
      +-----------+  +------------------+
                           |
                           v
                    +------------------+
                    | SUGGEST          |
                    | Closest valid    |
                    | name alternative |
                    +------------------+
```

### Validation Rules

| Rule | Description | Error Message |
|------|-------------|---------------|
| Prefix Check | Name must start with `grp-`, `svr-`, or `rng-` | "Invalid prefix: must be grp-, svr-, or rng-" |
| Segment Count | Must have exactly 5 segments (prefix-AppID-NH-SZ-Subtype) | "Invalid format: expected 5 segments" |
| AppID Valid | AppID must exist in the application registry | "Unknown AppID: {value}" |
| NH Valid | NH must be NH01 through NH17 | "Invalid Neighbourhood: {value}" |
| SZ Valid | SZ must be a recognized security zone code | "Invalid Security Zone: {value}" |
| Subtype Valid | For groups, subtype must be in the approved list | "Invalid subtype: {value}" |
| Case Check | All segments must be uppercase | "Name must be uppercase" |
| Character Check | Only alphanumeric characters and hyphens allowed | "Invalid characters detected" |

---

## 3. Rule Certification Workflow

### Overview
The periodic certification workflow ensures all active firewall rules remain necessary and compliant.

### Workflow Diagram

```
         +---------------------------+
         | CERTIFICATION TRIGGER     |
         | (Periodic / On-demand)    |
         +------------+--------------+
                      |
                      v
         +---------------------------+
         | Select Rules for          |
         | Certification             |
         | (Filter by expiry date)   |
         +------------+--------------+
                      |
                      v
         +---------------------------+
         | For Each Rule:            |
         +------------+--------------+
                      |
                      v
         +---------------------------+
         | Check Naming Standards    |
         | Compliance                |
         +------------+--------------+
                      |
               +------+------+
               |             |
          [Compliant]   [Non-Compliant]
               |             |
               v             v
         +-----------+ +-----------------+
         | Continue  | | Flag for        |
         | Review    | | Remediation     |
         +-----------+ | Assign to Owner |
               |       +-----------------+
               v             |
         +---------------------------+
         | Check Group-to-Group      |
         | Enforcement               |
         +------------+--------------+
                      |
               +------+------+
               |             |
            [G2G]      [Non-G2G]
               |             |
               v             v
         +-----------+ +-----------------+
         | Continue  | | Requires        |
         |           | | Exception       |
         +-----------+ | Approval        |
               |       +---------+-------+
               |                 |
               v                 v
         +---------------------------+
         | Security Analyst Review   |
         +------------+--------------+
                      |
               +------+------+
               |             |
          [Certify]     [Reject]
               |             |
               v             v
         +-----------+ +-----------------+
         | Status:   | | Status:         |
         | CERTIFIED | | EXPIRED /       |
         | Set new   | | REVOKED         |
         | expiry    | | Notify owner    |
         +-----------+ +-----------------+
               |             |
               v             v
         +---------------------------+
         | Update Audit Trail        |
         | Record certification      |
         | action and timestamp      |
         +---------------------------+
                      |
                      v
                    END
```

### Certification Status Matrix

| Current Status | Action | New Status | Notification |
|---------------|--------|------------|-------------|
| Certified | Recertify | Certified (renewed) | Owner notified of renewal |
| Certified | Reject | Revoked | Owner + Engineer notified |
| Pending Review | Certify | Certified | Engineer notified |
| Pending Review | Reject | Rejected | Engineer notified with reason |
| Expired | Recertify | Certified (renewed) | Owner notified of renewal |
| Expired | No Action | Disabled | Auto-disabled after grace period |

---

## 4. Change Request (CHG) Submission Workflow

### Overview
The workflow for submitting firewall rule changes through ServiceNow integration.

### Workflow Diagram

```
         +---------------------------+
         | Rule Status: CERTIFIED    |
         +------------+--------------+
                      |
                      v
         +---------------------------+
         | Engineer clicks           |
         | "Submit CHG"              |
         +------------+--------------+
                      |
                      v
         +---------------------------+
         | Generate CHG Payload      |
         +---------------------------+
         | - Rule details            |
         | - Source/destination       |
         | - Port/protocol           |
         | - Compliance status       |
         | - Certification ref       |
         | - Risk assessment         |
         | - Implementation plan     |
         | - Rollback plan           |
         +------------+--------------+
                      |
                      v
         +---------------------------+
         | Validate CHG              |
         | Prerequisites             |
         +------------+--------------+
                      |
               +------+------+
               |             |
           [Valid]      [Missing Info]
               |             |
               v             v
         +-----------+ +-----------------+
         | Submit to | | Return to       |
         | ServiceNow| | Rule Editor     |
         +-----------+ | Show missing    |
               |       | fields          |
               v       +-----------------+
         +---------------------------+
         | ServiceNow Processing     |
         +---------------------------+
         | - CHG ticket created      |
         | - Assign to SNS team      |
         | - CAB review scheduled    |
         +------------+--------------+
                      |
                      v
         +---------------------------+
         | Rule Status:              |
         | CHG_SUBMITTED             |
         | CHG Number: CHG0012345    |
         +------------+--------------+
                      |
                      v
         +---------------------------+
         | Monitor CHG Status        |
         | (Periodic polling)        |
         +------------+--------------+
                      |
               +------+------+
               |             |
          [Approved]    [Rejected]
               |             |
               v             v
         +-----------+ +-----------------+
         | Deploy    | | Status:         |
         | Rules     | | CHG_REJECTED    |
         | to NGDC   | | Notify engineer |
         +-----------+ +-----------------+
               |
               v
         +---------------------------+
         | Rule Status: DEPLOYED     |
         | Deployment timestamp      |
         | GitOps commit ref         |
         +---------------------------+
                      |
                      v
                    END
```

### CHG Request Fields

| Field | Source | Required |
|-------|--------|----------|
| Short Description | Auto-generated from rule name | Yes |
| Description | Rule details + compliance summary | Yes |
| Category | "Network - Firewall" | Yes |
| Assignment Group | SNS Team (based on NH/SZ) | Yes |
| Risk | Auto-calculated from SZ risk level | Yes |
| Implementation Plan | Generated from rule config | Yes |
| Rollback Plan | Auto-generated reverse rule | Yes |
| Test Plan | Connectivity test commands | Yes |
| Requested By | Current user | Yes |
| Configuration Items | Source and destination CIs | Yes |

---

## 5. Legacy Rule Migration Workflow

### Overview
The workflow for migrating existing legacy firewall rules to modernized NGDC standards.

### Workflow Diagram

```
         +---------------------------+
         | MIGRATION STUDIO          |
         | Select Legacy DC          |
         +---------------------------+
         | - DC LEGACY A              |
         | - DC LEGACY B             |
         | - DC LEGACY C           |
         | - DC LEGACY D             |
         | - DC LEGACY E          |
         | - DC LEGACY F             |
         +------------+--------------+
                      |
                      v
         +---------------------------+
         | Load Legacy Rules         |
         | from selected DC          |
         +------------+--------------+
                      |
                      v
         +---------------------------+
         | Display in Migration      |
         | Rule Table                |
         | - Show source/dest IPs    |
         | - Show ports/protocols    |
         | - Show current status     |
         +------------+--------------+
                      |
                      v
         +---------------------------+
         | Select Rules for          |
         | Migration (multi-select)  |
         +------------+--------------+
                      |
                      v
         +---------------------------+
         | Open Migration Details    |
         | Form                      |
         +---------------------------+
         | - Select target app       |
         | - Select target NH        |
         | - Select target SZ        |
         | - Review naming standards |
         +------------+--------------+
                      |
                      v
         +---------------------------+
         | Standards Compliance      |
         | Analysis                  |
         +------------+--------------+
                      |
         +------------+------------+
         |            |            |
    [Compliant]  [Partially]  [Non-Compliant]
         |       [Compliant]       |
         |            |            |
         v            v            v
    +---------+ +-----------+ +------------------+
    | Direct  | | Auto-     | | Manual           |
    | Map     | | Suggest   | | Intervention     |
    | to NGDC | | Fixes     | | Required         |
    +---------+ +-----------+ +------------------+
         |            |            |
         |            v            v
         |     +-----------+ +------------------+
         |     | Apply     | | User edits       |
         |     | Suggested | | mapping manually |
         |     | Names     | | with builder UI  |
         |     +-----------+ +------------------+
         |            |            |
         +-----+------+-----+-----+
               |
               v
         +---------------------------+
         | Generate Migration Plan   |
         +---------------------------+
         | For each rule:            |
         | - Old: 10.1.2.0/24       |
         |   New: grp-APP001-NH01-  |
         |        CDE-WEB           |
         | - Old: 10.5.6.100        |
         |   New: svr-APP001-NH05-  |
         |        GEN-DBPROD01      |
         +------------+--------------+
                      |
                      v
         +---------------------------+
         | Validate Migration Plan   |
         +---------------------------+
         | - All names compliant     |
         | - All NH/SZ valid         |
         | - No policy violations    |
         | - G2G enforcement met     |
         +------------+--------------+
                      |
               +------+------+
               |             |
           [Valid]      [Has Issues]
               |             |
               v             v
         +-----------+ +-----------------+
         | Execute   | | Show Issues     |
         | Migration | | Return to Edit  |
         +-----------+ +-----------------+
               |
               v
         +---------------------------+
         | Create New NGDC Rules     |
         | - Status: DRAFT           |
         | - Link to legacy rule     |
         | - Audit trail populated   |
         +---------------------------+
         | Mark Legacy Rules as      |
         | MIGRATED                  |
         +---------------------------+
                      |
                      v
                    END
```

### Migration Mapping Table

| Legacy DC | Target NGDC | Migration Status |
|-----------|------------|-----------------|
| DC LEGACY A | ALPHA NGDC | Active migration |
| DC LEGACY B | ALPHA NGDC | Active migration |
| DC LEGACY C | GAMMA NGDC | Active migration |
| DC LEGACY D | ALPHA NGDC | Active migration |
| DC LEGACY E | ALPHA NGDC | Active migration |
| DC LEGACY F | BETA NGDC | Active migration |

### Migration Compliance Levels

| Level | Description | Action Required |
|-------|-------------|----------------|
| **Fully Compliant** | All names follow standards, G2G enforced | Direct migration |
| **Partially Compliant** | Some names need updating | Auto-suggest + user review |
| **Non-Compliant** | Major rework needed | Manual remapping with builder UI |

---

## 6. NH/SZ Decision Engine Workflow

### Overview
The automated decision engine that determines the appropriate Neighbourhood and Security Zone for an application.

### Workflow Diagram

```
         +---------------------------+
         | INPUT: Application        |
         | Attributes                |
         +---------------------------+
         | - PAA Zone                |
         | - @Exposure               |
         | - PCI Compliance Flag     |
         | - Data Classification     |
         | - Criticality Rating      |
         +------------+--------------+
                      |
                      v
         +---------------------------+
         | Step 1: Check PCI         |
         | Compliance                |
         +------------+--------------+
                      |
               +------+------+
               |             |
         [PCI=Yes]     [PCI=No]
               |             |
               v             |
         +-----------+       |
         | SZ = CDE  |       |
         | NH = NH13 |       |
         +-----------+       |
                             v
                   +-------------------+
                   | Step 2: Check     |
                   | PAA Zone          |
                   +--------+----------+
                            |
                   +--------+--------+--------+
                   |        |        |        |
              [External] [Internal] [Payment] [None]
                   |        |        |        |
                   v        v        v        v
              +------+ +------+ +------+ +--------+
              |EPAA  | |LPAA  | |UCPA  | |Continue|
              |NH12  | |NH03  | |NH13  | |        |
              +------+ +------+ +------+ +--------+
                                              |
                                              v
                                   +-------------------+
                                   | Step 3: Check     |
                                   | @Exposure         |
                                   +--------+----------+
                                            |
                                   +--------+--------+
                                   |                 |
                              [External]        [Internal]
                                   |                 |
                                   v                 v
                              +--------+       +---------+
                              | SZ=DMZ |       | Continue|
                              | NH=NH02|       |         |
                              | or     |       +---------+
                              | NH=NH12|            |
                              +--------+            v
                                          +-------------------+
                                          | Step 4: Check     |
                                          | Data Class.       |
                                          +--------+----------+
                                                   |
                                          +--------+--------+
                                          |        |        |
                                     [Critical] [Conf.] [Standard]
                                          |        |        |
                                          v        v        v
                                     +------+ +------+ +------+
                                     |RST   | |RST   | |GEN   |
                                     |NH05  | |NH07  | |NH03  |
                                     |or    | |      | |or    |
                                     |NH09  | +------+ |NH01  |
                                     +------+          +------+
```

### Decision Matrix

| PCI | PAA Zone | @Exposure | Data Class | Criticality | -> NH | -> SZ |
|-----|----------|-----------|------------|-------------|-------|-------|
| Yes | Any | Any | Any | Any | NH13 | CDE |
| No | External | External | Any | Any | NH12 | EPAA |
| No | Internal | Internal | Any | Any | NH03 | LPAA |
| No | Payment | Any | Any | Any | NH13 | UCPA |
| No | None | External | Any | Any | NH02/NH12 | DMZ |
| No | None | Internal | Critical | High | NH05/NH09 | RST |
| No | None | Internal | Confidential | Any | NH07 | RST |
| No | None | Internal | Standard | Any | NH03/NH01 | GEN |

---

## 7. Group-to-Group Enforcement Workflow

### Overview
The enforcement workflow ensuring all firewall rules reference groups rather than individual IPs or subnets.

### Workflow Diagram

```
         +---------------------------+
         | New Rule / Rule Update    |
         +------------+--------------+
                      |
                      v
         +---------------------------+
         | Extract Source Object     |
         +------------+--------------+
                      |
                      v
         +---------------------------+
         | Check Source Prefix       |
         +------------+--------------+
                      |
               +------+------+
               |             |
          [grp-*]       [svr-* or
               |         rng-* or
               |         raw IP]
               |             |
               v             v
         +-----------+ +-----------------+
         | Source     | | Source is       |
         | is Group  | | NOT a Group     |
         | OK        | | Flag            |
         +-----------+ +-----------------+
               |             |
               v             v
         +---------------------------+
         | Extract Destination Obj   |
         +------------+--------------+
                      |
                      v
         +---------------------------+
         | Check Destination Prefix  |
         +------------+--------------+
                      |
               +------+------+
               |             |
          [grp-*]       [svr-* or
               |         rng-* or
               |         raw IP]
               |             |
               v             v
         +-----------+ +-----------------+
         | Dest      | | Dest is         |
         | is Group  | | NOT a Group     |
         | OK        | | Flag            |
         +-----------+ +-----------------+
               |             |
               v             v
         +---------------------------+
         | Evaluate G2G Status       |
         +------------+--------------+
                      |
         +------------+------------+
         |            |            |
    [Both Group] [One Non-Grp] [Both Non-Grp]
         |            |            |
         v            v            v
    +---------+ +-----------+ +------------------+
    |COMPLIANT| | EXCEPTION | | NON-COMPLIANT    |
    |         | | NEEDED    | | Blocked unless   |
    | Green   | |           | | exception        |
    | Badge   | | Amber     | | approved         |
    |         | | Badge     | |                  |
    | No      | |           | | Red Badge        |
    | action  | | Requires  | |                  |
    | needed  | | Security  | | Requires         |
    |         | | Analyst   | | Security Analyst |
    |         | | Approval  | | + Manager        |
    |         | |           | | Approval         |
    +---------+ +-----------+ +------------------+
```

### Enforcement Rules

| Scenario | Source Type | Dest Type | Status | Action Required |
|----------|-----------|-----------|--------|----------------|
| Ideal | `grp-*` | `grp-*` | Compliant | None |
| Exception | `grp-*` | `svr-*` | Needs Exception | Security Analyst approval |
| Exception | `svr-*` | `grp-*` | Needs Exception | Security Analyst approval |
| Exception | `grp-*` | `rng-*` | Needs Exception | Security Analyst approval |
| Non-Compliant | `svr-*` | `svr-*` | Blocked | Security Analyst + Manager approval |
| Non-Compliant | Raw IP | Any | Blocked | Full exception process |

---

## 8. Rule Lifecycle State Machine

### Overview
The complete state machine showing all possible states and transitions for a firewall rule.

### State Diagram

```
                          +----------+
                          |  DRAFT   |<----------------------------------+
                          +----+-----+                                   |
                               |                                         |
                    [Submit for Review]                                   |
                               |                                    [Reject &
                               v                                     Revise]
                     +------------------+                                |
                     | PENDING REVIEW   +--------------------------------+
                     +--------+---------+
                              |
                   [Security Analyst Review]
                              |
                    +---------+---------+
                    |                   |
               [Certify]          [Reject]
                    |                   |
                    v                   v
             +-----------+      +-----------+
             | CERTIFIED |      | REJECTED  |
             +-----+-----+      +-----------+
                   |                   |
          [Submit CHG Request]    [Edit & Resubmit]
                   |                   |
                   v                   v
          +-----------------+       DRAFT
          | CHG_SUBMITTED   |
          +--------+--------+
                   |
          +--------+--------+
          |                 |
     [CHG Approved]   [CHG Rejected]
          |                 |
          v                 v
     +-----------+   +--------------+
     | DEPLOYED  |   | CHG_REJECTED |
     +-----+-----+   +--------------+
           |                |
    [Cert. Expires]   [Re-submit CHG]
           |                |
           v                v
     +-----------+    CHG_SUBMITTED
     | EXPIRED   |
     +-----+-----+
           |
    +------+------+
    |             |
 [Recertify]  [Disable]
    |             |
    v             v
 CERTIFIED  +-----------+
            | DISABLED  |
            +-----+-----+
                  |
           [Reactivate]
                  |
                  v
               DRAFT
```

### State Definitions

| State | Description | Allowed Actions |
|-------|-------------|----------------|
| **DRAFT** | Rule created, not yet submitted | Edit, Delete, Submit for Review |
| **PENDING REVIEW** | Awaiting security analyst review | Certify, Reject |
| **CERTIFIED** | Approved by security analyst | Submit CHG, Edit (creates new version) |
| **REJECTED** | Failed security review | Edit & Resubmit, Delete |
| **CHG_SUBMITTED** | Change request submitted to ServiceNow | Monitor status |
| **CHG_REJECTED** | Change request rejected by CAB | Re-submit CHG, Edit |
| **DEPLOYED** | Rule deployed to NGDC firewalls | Monitor, Recertify when expired |
| **EXPIRED** | Certification period elapsed | Recertify, Disable |
| **DISABLED** | Rule deactivated | Reactivate (goes to DRAFT), Delete |
| **MIGRATED** | Legacy rule migrated to new format | (Terminal state for legacy) |

---

## 9. Drag-and-Drop Destination Workflow

### Overview
The interactive drag-and-drop interface for configuring rule destinations.

### Workflow Diagram

```
    +--------------------------------------------------------------+
    |                DESIGN STUDIO - DESTINATIONS                   |
    +--------------------------------------------------------------+
    |                                                              |
    |  +------ AVAILABLE TARGETS --------+  +-- DROP ZONE ------+ |
    |  |                                 |  |                    | |
    |  | +-----------------------------+ |  | +--------------+   | |
    |  | | NGDC Groups (grp-*)         | |  | | Destination  |   | |
    |  | | +-------------------------+ | |  | | List         |   | |
    |  | | | grp-APP001-NH01-CDE-WEB | | |  | |              |   | |
    |  | | | grp-APP001-NH01-CDE-APP | | |  | | [Drop items  |   | |
    |  | | | grp-APP002-NH05-GEN-DB  | | |  | |  here]       |   | |
    |  | | +-------------------------+ | |  | |              |   | |
    |  | +-----------------------------+ |  | | +----------+ |   | |
    |  |                                 |  | | |Dropped #1| |   | |
    |  | +-----------------------------+ |  | | +----------+ |   | |
    |  | | Birthright Groups           | |  | | +----------+ |   | |
    |  | | +-------------------------+ | |  | | |Dropped #2| |   | |
    |  | | | grp-INFRA-NH08-MGT-MON  | | |  | | +----------+ |   | |
    |  | | | grp-INFRA-NH08-MGT-DNS  | | |  | |              |   | |
    |  | | +-------------------------+ | |  | +--------------+   | |
    |  | +-----------------------------+ |  |                    | |
    |  |                                 |  | +--------------+   | |
    |  | +-----------------------------+ |  | | Custom Dest  |   | |
    |  | | Custom Destination          | |  | | [+ Add new]  |   | |
    |  | | [+ Add Custom Target]       | |  | +--------------+   | |
    |  | +-----------------------------+ |  |                    | |
    |  +---------------------------------+  +--------------------+ |
    |                                                              |
    +--------------------------------------------------------------+
                               |
                               v
                  +---------------------------+
                  | On Drop:                  |
                  | 1. Validate G2G           |
                  | 2. Check naming standards |
                  | 3. Add to destination list|
                  | 4. Update policy canvas   |
                  +---------------------------+
```

### Drag-and-Drop Events

| Event | Action | Validation |
|-------|--------|-----------|
| **Drag Start** | Highlight available drop zones | Verify source has items |
| **Drag Over** | Show drop indicator | Check compatibility |
| **Drop** | Add to destination list | G2G check, naming validation |
| **Custom Add** | Open custom destination form | Full naming standards validation |
| **Remove** | Remove from destination list | Update policy canvas |

---

## 10. End-to-End Application Workflow

### Overview
The complete end-to-end workflow showing how all components interact in a typical usage scenario.

### Workflow Diagram

```
+=========================================================================+
|                    END-TO-END WORKFLOW                                   |
+=========================================================================+
|                                                                         |
|  PHASE 1: DESIGN                                                        |
|  +-----------------------------------------------------------------+    |
|  |                                                                 |    |
|  |  [1] App Owner submits firewall rule request                    |    |
|  |       |                                                         |    |
|  |  [2] Network Engineer opens Design Studio                      |    |
|  |       |                                                         |    |
|  |  [3] Select Application -> Auto-populate NH/SZ                 |    |
|  |       |                                                         |    |
|  |  [4] Build compliant source name (Naming Standards Builder)    |    |
|  |       |                                                         |    |
|  |  [5] Drag-and-drop destinations (Group-to-Group enforced)      |    |
|  |       |                                                         |    |
|  |  [6] Configure ports, protocols, action                        |    |
|  |       |                                                         |    |
|  |  [7] Create Rule -> Status: DRAFT                              |    |
|  |                                                                 |    |
|  +-----------------------------------------------------------------+    |
|       |                                                                 |
|       v                                                                 |
|  PHASE 2: REVIEW & CERTIFICATION                                       |
|  +-----------------------------------------------------------------+    |
|  |                                                                 |    |
|  |  [8] Engineer submits rule for review                          |    |
|  |       |                                                         |    |
|  |  [9] Security Analyst reviews:                                 |    |
|  |       - Naming standards compliance (Green/Red)                |    |
|  |       - Group-to-group compliance (Green/Amber/Red)            |    |
|  |       - Policy matrix validation                               |    |
|  |       - Risk assessment                                        |    |
|  |       |                                                         |    |
|  | [10] Certify or Reject rule                                    |    |
|  |       |                                                         |    |
|  | [11] If Certified -> Status: CERTIFIED                         |    |
|  |                                                                 |    |
|  +-----------------------------------------------------------------+    |
|       |                                                                 |
|       v                                                                 |
|  PHASE 3: CHANGE MANAGEMENT                                            |
|  +-----------------------------------------------------------------+    |
|  |                                                                 |    |
|  | [12] Engineer submits CHG request                              |    |
|  |       |                                                         |    |
|  | [13] ServiceNow ticket created automatically                   |    |
|  |       - Assigned to SNS team                                   |    |
|  |       - Risk assessment attached                               |    |
|  |       - Implementation plan generated                          |    |
|  |       |                                                         |    |
|  | [14] CAB reviews and approves/rejects                          |    |
|  |       |                                                         |    |
|  | [15] If Approved -> Status: CHG_APPROVED                       |    |
|  |                                                                 |    |
|  +-----------------------------------------------------------------+    |
|       |                                                                 |
|       v                                                                 |
|  PHASE 4: DEPLOYMENT                                                    |
|  +-----------------------------------------------------------------+    |
|  |                                                                 |    |
|  | [16] Rules committed to GitOps repository                      |    |
|  |       |                                                         |    |
|  | [17] CI/CD pipeline deploys to NGDC firewalls                  |    |
|  |       |                                                         |    |
|  | [18] Deployment verified -> Status: DEPLOYED                   |    |
|  |       |                                                         |    |
|  | [19] Audit trail updated with deployment details               |    |
|  |                                                                 |    |
|  +-----------------------------------------------------------------+    |
|       |                                                                 |
|       v                                                                 |
|  PHASE 5: ONGOING MANAGEMENT                                           |
|  +-----------------------------------------------------------------+    |
|  |                                                                 |    |
|  | [20] Periodic certification reminders sent                     |    |
|  |       |                                                         |    |
|  | [21] Rule owner/analyst recertifies or disables                |    |
|  |       |                                                         |    |
|  | [22] If expired and not recertified -> Auto-disable            |    |
|  |       |                                                         |    |
|  | [23] All actions recorded in audit history                     |    |
|  |                                                                 |    |
|  +-----------------------------------------------------------------+    |
|                                                                         |
+=========================================================================+
```

### Phase Summary

| Phase | Duration | Primary Actor | Key Deliverable |
|-------|----------|--------------|-----------------|
| **Design** | 15-30 min | Network Engineer | Draft firewall rule with compliant naming |
| **Review** | 1-3 days | Security Analyst | Certified rule |
| **Change Mgmt** | 3-5 days | Change Manager / CAB | Approved CHG ticket |
| **Deployment** | 1-2 hours | Automated (CI/CD) | Deployed rule on NGDC firewalls |
| **Ongoing** | Periodic (90 days) | Rule Owner / Analyst | Recertified or disabled rule |

---

*This document is maintained as part of the Network Firewall Studio documentation suite and should be reviewed quarterly.*
