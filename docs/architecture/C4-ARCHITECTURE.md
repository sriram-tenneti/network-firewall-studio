# Network Firewall Studio - C4 Model Architecture

## Document Control

| Property | Value |
|----------|-------|
| **Document Title** | Network Firewall Studio - C4 Architecture Model |
| **Version** | 1.0.0 |
| **Classification** | Internal - Architecture |
| **Author** | Network Engineering Team |
| **Last Updated** | 2026-03-13 |
| **Status** | Approved |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [C4 Model Overview](#2-c4-model-overview)
3. [Level 1: System Context Diagram](#3-level-1-system-context-diagram)
4. [Level 2: Container Diagram](#4-level-2-container-diagram)
5. [Level 3: Component Diagram - Backend](#5-level-3-component-diagram---backend)
6. [Level 3: Component Diagram - Frontend](#6-level-3-component-diagram---frontend)
7. [Level 4: Code Diagram - Naming Standards Engine](#7-level-4-code-diagram---naming-standards-engine)
8. [Level 4: Code Diagram - NGDC Data Model](#8-level-4-code-diagram---ngdc-data-model)
9. [Deployment Architecture](#9-deployment-architecture)
10. [Security Architecture](#10-security-architecture)
11. [Data Flow Architecture](#11-data-flow-architecture)
12. [Appendix](#12-appendix)

---

## 1. Executive Summary

The **Network Firewall Studio** is an enterprise-grade web application designed to modernize and streamline the lifecycle management of network firewall rules. It provides capabilities for:

- **New Rule Design**: Drag-and-drop interface for creating firewall rules with strict naming standards enforcement
- **Migration Management**: Automated migration of legacy firewall rules from Legacy Data Centers to modernized NGDC infrastructure
- **Standards Enforcement**: Comprehensive naming standards engine with group-to-group policy enforcement
- **Rule Certification**: Periodic certification workflows to ensure compliance and recertification of existing rules
- **Change Management**: Integration with ServiceNow for CHG request submission and tracking
- **GitOps Integration**: Repository-based rule storage and version control

The architecture follows the **C4 Model** (Context, Containers, Components, Code) to provide progressive levels of detail from system-level interactions down to code-level implementation.

---

## 2. C4 Model Overview

The C4 model provides four levels of abstraction for describing the software architecture:

| Level | Name | Purpose | Audience |
|-------|------|---------|----------|
| **Level 1** | System Context | How the system fits into the world | Everyone |
| **Level 2** | Container | High-level technology choices | Technical stakeholders |
| **Level 3** | Component | Internal structure of containers | Developers, architects |
| **Level 4** | Code | Implementation details | Developers |

---

## 3. Level 1: System Context Diagram

### Description

The System Context diagram shows the Network Firewall Studio as a central system and its interactions with external actors and systems.

### Diagram

```
+----------------------------------------------------------+
|                   EXTERNAL SYSTEMS                        |
+----------------------------------------------------------+

    +-------------------+         +---------------------+
    |  Network Engineer |         |  Security Analyst   |
    |    (Primary User) |         |  (Rule Reviewer)    |
    +--------+----------+         +----------+----------+
             |                               |
             |  Creates/manages              |  Reviews/certifies
             |  firewall rules               |  firewall rules
             |                               |
             v                               v
    +--------------------------------------------------------+
    |                                                        |
    |          NETWORK FIREWALL STUDIO                       |
    |                                                        |
    |  - Design Studio (New Rule Creation)                   |
    |  - Migration Studio (Legacy to NGDC)                   |
    |  - Rule Certification Engine                           |
    |  - Standards Enforcement Engine                        |
    |  - Change Management Integration                       |
    |                                                        |
    +------+-----------+-----------+-----------+-------------+
           |           |           |           |
           v           v           v           v
    +----------+ +----------+ +---------+ +-----------+
    |ServiceNow| |  GitOps  | |  NGDC   | |  Legacy   |
    |  (ITSM)  | |  Repo    | | Firewall| |  Firewall |
    |          | |          | | Infra   | |  Systems  |
    +----------+ +----------+ +---------+ +-----------+
    Submit CHG   Store rules   Deploy      Import
    requests     as code       rules       existing rules
```

### External Actors

| Actor | Role | Interaction |
|-------|------|-------------|
| **Network Engineer** | Primary user | Creates, modifies, and manages firewall rules through the Design Studio and Migration Studio |
| **Security Analyst** | Reviewer/Approver | Reviews firewall rule requests, certifies rules, approves exceptions to group-to-group policy |
| **Change Manager** | Approver | Reviews and approves Change Requests (CHGs) submitted through ServiceNow integration |
| **Application Owner** | Requestor | Initiates firewall rule requests for their applications |

### External Systems

| System | Purpose | Integration Type |
|--------|---------|-----------------|
| **ServiceNow (ITSM)** | Change management and ticketing | REST API - CHG request submission |
| **GitOps Repository** | Rule version control and deployment pipeline | Git API - Rule storage as code |
| **NGDC Firewall Infrastructure** | Target deployment infrastructure | API - Rule deployment and status |
| **Legacy Firewall Systems** | Source of existing rules for migration | Data Import - Rule extraction |
| **LDAP/Active Directory** | User authentication and authorization | LDAP/SAML - SSO integration |

---

## 4. Level 2: Container Diagram

### Description

The Container diagram shows the high-level shape of the software architecture and how responsibilities are distributed. Each container is a separately deployable/runnable unit.

### Diagram

```
+------------------------------------------------------------------+
|                    NETWORK FIREWALL STUDIO                        |
+------------------------------------------------------------------+
|                                                                  |
|  +--------------------------+   +-----------------------------+  |
|  |   FRONTEND APPLICATION   |   |    BACKEND API SERVICE      |  |
|  |   (React + TypeScript)   |   |    (FastAPI + Python)       |  |
|  |                          |   |                             |  |
|  | +--------------------+   |   | +------------------------+  |  |
|  | | Design Studio      |   |   | | REST API Layer         |  |  |
|  | | - Source Panel      |   |   | | - /api/firewall-rules  |  |  |
|  | | - Destination Panel |   |   | | - /api/migration       |  |  |
|  | | - Policy Canvas     |   |   | | - /api/reference       |  |  |
|  | | - Rule Lifecycle    |   |   | | - /api/naming-standards|  |  |
|  | +--------------------+   |   | +------------------------+  |  |
|  |                          |   |                             |  |
|  | +--------------------+   |   | +------------------------+  |  |
|  | | Migration Studio   |   |   | | Business Logic Layer   |  |  |
|  | | - Legacy Rules     |<--+-->| | - Naming Standards Eng.|  |  |
|  | | - NGDC Sidebar     |   |   | | - Policy Validation    |  |  |
|  | | - Migration Planner|   |   | | - Migration Engine     |  |  |
|  | | - Details Form     |   |   | | - Rule Lifecycle Mgr   |  |  |
|  | +--------------------+   |   | +------------------------+  |  |
|  |                          |   |                             |  |
|  | +--------------------+   |   | +------------------------+  |  |
|  | | Shared Components  |   |   | | Data Layer             |  |  |
|  | | - Action Bar       |   |   | | - NGDC Registry        |  |  |
|  | | - History Modal    |   |   | | - Neighbourhood Data   |  |  |
|  | | - Naming Builder   |   |   | | - Security Zones       |  |  |
|  | +--------------------+   |   | | - Legacy DC Data       |  |  |
|  |                          |   | +------------------------+  |  |
|  +--------------------------+   +-----------------------------+  |
|                                                                  |
|  Technology Stack:                                               |
|  Frontend: React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui  |
|  Backend: FastAPI, Python 3.12, Poetry, Uvicorn                  |
|  Communication: REST API (JSON over HTTPS)                       |
|  Authentication: Bearer Token / SAML SSO                         |
+------------------------------------------------------------------+
```

### Container Details

| Container | Technology | Purpose | Port |
|-----------|-----------|---------|------|
| **Frontend Application** | React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui | Single Page Application providing the user interface for all firewall management operations | 5173 (dev) / 80 (prod) |
| **Backend API Service** | FastAPI + Python 3.12 + Poetry + Uvicorn | RESTful API service providing business logic, data management, and integration orchestration | 8000 |
| **In-Memory Database** | Python dictionaries (PoC) / PostgreSQL (Production) | Data persistence for rules, configurations, and audit trails | N/A |

### Communication Protocols

| From | To | Protocol | Purpose |
|------|-----|----------|---------|
| Frontend | Backend | HTTPS REST (JSON) | All API operations |
| Backend | ServiceNow | HTTPS REST | CHG request submission |
| Backend | GitOps Repo | Git/HTTPS | Rule storage and versioning |
| Backend | NGDC Infra | HTTPS REST | Rule deployment |

---

## 5. Level 3: Component Diagram - Backend

### Description

The Component diagram shows how the Backend API Service container is internally structured.

### Diagram

```
+----------------------------------------------------------------------+
|                     BACKEND API SERVICE                               |
|                     (FastAPI + Python 3.12)                           |
+----------------------------------------------------------------------+
|                                                                      |
|  +---------------------------- API ROUTES --------------------------+|
|  |                                                                  ||
|  |  +------------------+  +------------------+  +----------------+  ||
|  |  | firewall_rules.py|  | migration.py     |  | reference.py   |  ||
|  |  |                  |  |                  |  |                |  ||
|  |  | POST /rules      |  | GET /legacy-rules|  | GET /nh        |  ||
|  |  | GET  /rules      |  | POST /validate   |  | GET /sz        |  ||
|  |  | PUT  /rules/{id} |  | POST /map        |  | GET /apps      |  ||
|  |  | DELETE /rules/{id}|  | POST /execute    |  | GET /naming-std|  ||
|  |  | POST /certify    |  | GET /status       |  | POST /validate |  ||
|  |  | POST /submit-chg |  |                  |  | POST /generate |  ||
|  |  | GET  /history    |  |                  |  | POST /suggest  |  ||
|  |  +--------+---------+  +--------+---------+  | POST /det-zone |  ||
|  |           |                      |            +--------+-------+  ||
|  +-----------+----------------------+---------------------+----------+|
|              |                      |                     |           |
|  +--------------------------- SERVICES -----------------------------+|
|  |           |                      |                     |          ||
|  |  +--------v---------+  +--------v---------+  +--------v-------+  ||
|  |  | Rule Lifecycle   |  | Migration Engine |  | Naming Stds    |  ||
|  |  | Manager          |  |                  |  | Engine         |  ||
|  |  |                  |  | - Legacy parser  |  |                |  ||
|  |  | - Create rule    |  | - NH/SZ mapper   |  | - validate()   |  ||
|  |  | - Validate rule  |  | - Standards check|  | - generate()   |  ||
|  |  | - Certify rule   |  | - Migration plan |  | - suggest()    |  ||
|  |  | - Submit CHG     |  | - Execute migrate|  | - determine_sz |  ||
|  |  | - Track history  |  |                  |  | - check_g2g()  |  ||
|  |  +--------+---------+  +--------+---------+  +--------+-------+  ||
|  |           |                      |                     |          ||
|  +-----------+----------------------+---------------------+----------+|
|              |                      |                     |           |
|  +--------------------------- DATA LAYER ----------------------------+|
|  |                                                                   ||
|  |  +-------------------+  +------------------+  +-----------------+ ||
|  |  | NGDC Registry     |  | Rule Store       |  | Config Store    | ||
|  |  |                   |  |                  |  |                 | ||
|  |  | - 17 Neighbourhoods|  | - Firewall Rules |  | - Naming Stds  | ||
|  |  | - 17 Security Zones|  | - Rule History   |  | - NGDC Matrix  | ||
|  |  | - 3 NGDC DCs      |  | - Certifications |  | - Policy Config| ||
|  |  | - 6 Legacy DCs    |  | - CHG Requests   |  | - Birthright   | ||
|  |  | - Applications    |  |                  |  |                 | ||
|  |  +-------------------+  +------------------+  +-----------------+ ||
|  +-------------------------------------------------------------------+|
+----------------------------------------------------------------------+
```

### Component Details

| Component | File | Responsibility |
|-----------|------|---------------|
| **Firewall Rules Router** | `app/routes/firewall_rules.py` | CRUD operations for firewall rules, certification, CHG submission, history tracking |
| **Migration Router** | `app/routes/migration.py` | Legacy rule import, validation, NH/SZ mapping, migration execution |
| **Reference Router** | `app/routes/reference.py` | Neighbourhoods, security zones, applications, naming standards, zone determination |
| **Naming Standards Engine** | `app/services/naming_standards.py` | Name validation, generation, suggestion, group-to-group enforcement |
| **NGDC Registry** | `app/database.py` | In-memory data store for all NGDC constructs, legacy DC data, applications |
| **Rule Store** | `app/database.py` | In-memory storage for firewall rules, history, and certification records |

---

## 6. Level 3: Component Diagram - Frontend

### Description

The Component diagram shows how the Frontend Application container is internally structured.

### Diagram

```
+----------------------------------------------------------------------+
|                    FRONTEND APPLICATION                               |
|                    (React 18 + TypeScript + Vite)                     |
+----------------------------------------------------------------------+
|                                                                      |
|  +--------------------------- PAGES --------------------------------+|
|  |                                                                  ||
|  |  +---------------------+        +----------------------------+   ||
|  |  | DesignStudioPage    |        | MigrationStudioPage        |   ||
|  |  |                     |        |                            |   ||
|  |  | - Rule creation     |        | - Legacy rule selection    |   ||
|  |  | - Drag-and-drop     |        | - NGDC mapping             |   ||
|  |  | - Standards builder |        | - Standards compliance     |   ||
|  |  | - Policy flow       |        | - Migration execution      |   ||
|  |  | - Rule lifecycle    |        | - Validation status        |   ||
|  |  +----------+----------+        +-------------+--------------+   ||
|  |             |                                  |                  ||
|  +-------------+----------------------------------+------------------+|
|                |                                  |                   |
|  +----------------------- COMPONENTS --------------------------------+|
|  |             |                                  |                  ||
|  |  +----------v----------+  +-------------------v----------------+ ||
|  |  | Design Studio       |  | Migration Studio                   | ||
|  |  | Components          |  | Components                         | ||
|  |  |                     |  |                                    | ||
|  |  | +----------------+  |  | +------------------+               | ||
|  |  | | SourcePanel    |  |  | | MigrationRuleTable|              | ||
|  |  | | - App selector |  |  | | - Legacy rules   |              | ||
|  |  | | - NH selector  |  |  | | - Status badges  |              | ||
|  |  | | - SZ display   |  |  | +------------------+              | ||
|  |  | | - Name builder |  |  |                                    | ||
|  |  | | - Name preview |  |  | +------------------+               | ||
|  |  | +----------------+  |  | | NGDCSidebar      |              | ||
|  |  |                     |  | | - NH list         |              | ||
|  |  | +----------------+  |  | | - SZ zones        |              | ||
|  |  | | DestinationPanel| |  | | - DC mappings    |              | ||
|  |  | | - Drag targets |  |  | +------------------+              | ||
|  |  | | - Drop zones   |  |  |                                    | ||
|  |  | | - Custom dest  |  |  | +------------------+               | ||
|  |  | | - Group enforce|  |  | | MigrationPlanner |              | ||
|  |  | +----------------+  |  | | - Mapping table  |              | ||
|  |  |                     |  | | - NH/SZ assign   |              | ||
|  |  | +----------------+  |  | +------------------+              | ||
|  |  | | PolicyFlowCanvas| |  |                                    | ||
|  |  | | - Visual flow  |  |  | +------------------+               | ||
|  |  | | - Rule preview |  |  | | MigrationDetails |              | ||
|  |  | +----------------+  |  | | - App selection  |              | ||
|  |  |                     |  | | - DC mapping     |              | ||
|  |  | +----------------+  |  | | - Standards form |              | ||
|  |  | | RuleLifecycle  |  |  | +------------------+              | ||
|  |  | | Table          |  |  |                                    | ||
|  |  | | - Rule list    |  |  +------------------------------------+ ||
|  |  | | - Compliance   |  |                                        ||
|  |  | | - Status       |  |                                        ||
|  |  | | - Actions      |  |                                        ||
|  |  | +----------------+  |                                        ||
|  |  +---------------------+                                        ||
|  +------------------------------------------------------------------+|
|                                                                      |
|  +----------------------- SHARED LAYER ------------------------------+|
|  |                                                                  ||
|  |  +-------------+  +------------+  +-----------+  +------------+  ||
|  |  | api.ts      |  | types/     |  | ActionBar |  | History    |  ||
|  |  | - REST calls|  | index.ts   |  | - Nav     |  | Modal      |  ||
|  |  | - Type-safe |  | - Interfaces| | - Actions |  | - Audit    |  ||
|  |  | - Error hdl |  | - Enums    |  | - Status  |  | - Timeline |  ||
|  |  +-------------+  +------------+  +-----------+  +------------+  ||
|  +------------------------------------------------------------------+|
+----------------------------------------------------------------------+
```

### Frontend Component Details

| Component | File | Responsibility |
|-----------|------|---------------|
| **DesignStudioPage** | `src/pages/DesignStudioPage.tsx` | Orchestrates the Design Studio view, manages state for rule creation workflow |
| **MigrationStudioPage** | `src/pages/MigrationStudioPage.tsx` | Orchestrates the Migration Studio view, manages legacy-to-NGDC migration workflow |
| **SourcePanel** | `src/components/design-studio/SourcePanel.tsx` | Application selection, neighbourhood selection, naming standards builder with real-time validation |
| **DestinationPanel** | `src/components/design-studio/DestinationPanel.tsx` | Drag-and-drop destination management, group-to-group enforcement, custom destination support |
| **PolicyFlowCanvas** | `src/components/design-studio/PolicyFlowCanvas.tsx` | Visual flow diagram showing source-to-destination policy rules |
| **RuleLifecycleTable** | `src/components/design-studio/RuleLifecycleTable.tsx` | Rule listing with compliance indicators (green/amber/red), status tracking, action buttons |
| **MigrationRuleTable** | `src/components/migration-studio/MigrationRuleTable.tsx` | Legacy rule display with selection for migration |
| **NGDCSidebar** | `src/components/migration-studio/NGDCSidebar.tsx` | NGDC neighbourhood and security zone reference panel |
| **MigrationPlannerTable** | `src/components/migration-studio/MigrationPlannerTable.tsx` | Migration mapping table with NH/SZ assignment |
| **MigrationDetailsForm** | `src/components/migration-studio/MigrationDetailsForm.tsx` | Detailed form for migration parameters and standards compliance |
| **API Layer** | `src/lib/api.ts` | Type-safe REST API client with full error handling |
| **Type Definitions** | `src/types/index.ts` | TypeScript interfaces for all data structures |

---

## 7. Level 4: Code Diagram - Naming Standards Engine

### Description

The Code diagram shows the internal structure of the Naming Standards Engine, the core enforcement module.

### Class/Function Diagram

```
+----------------------------------------------------------------------+
|              NAMING STANDARDS ENGINE                                  |
|              (app/services/naming_standards.py)                       |
+----------------------------------------------------------------------+
|                                                                      |
|  +------------------------+     +-------------------------------+    |
|  | VALIDATION FUNCTIONS   |     | GENERATION FUNCTIONS          |    |
|  +------------------------+     +-------------------------------+    |
|  |                        |     |                               |    |
|  | validate_group_name()  |     | generate_group_name()         |    |
|  | - Pattern: grp-{AppID} |     | - Input: app_id, nh, sz,     |    |
|  |   -{NH}-{SZ}-{Subtype} |     |   subtype                    |    |
|  | - Returns: valid/errors |     | - Output: grp-APP001-NH01-   |    |
|  |                        |     |   CDE-WEB                     |    |
|  | validate_server_name() |     |                               |    |
|  | - Pattern: svr-{AppID} |     | generate_server_name()        |    |
|  |   -{NH}-{SZ}-{Server}  |     | - Input: app_id, nh, sz,     |    |
|  | - Returns: valid/errors |     |   server_name                |    |
|  |                        |     | - Output: svr-APP001-NH01-   |    |
|  | validate_subnet_name() |     |   CDE-DBPROD01               |    |
|  | - Pattern: rng-{AppID} |     |                               |    |
|  |   -{NH}-{SZ}-{Desc}    |     | generate_subnet_name()       |    |
|  | - Returns: valid/errors |     | - Input: app_id, nh, sz,     |    |
|  |                        |     |   descriptor                  |    |
|  | validate_any_name()    |     | - Output: rng-APP001-NH01-   |    |
|  | - Auto-detect prefix   |     |   CDE-SUBNET01               |    |
|  | - Route to validator   |     |                               |    |
|  +------------------------+     +-------------------------------+    |
|                                                                      |
|  +------------------------+     +-------------------------------+    |
|  | ENFORCEMENT FUNCTIONS  |     | SUGGESTION FUNCTIONS          |    |
|  +------------------------+     +-------------------------------+    |
|  |                        |     |                               |    |
|  | check_group_to_group() |     | suggest_standard_name()       |    |
|  | - Input: source, dest  |     | - Input: non-compliant name   |    |
|  | - Check: both are grp- |     | - Output: closest compliant   |    |
|  | - Returns: compliant,  |     |   name suggestion              |    |
|  |   requires_exception   |     |                               |    |
|  |                        |     | determine_security_zone()     |    |
|  | validate_rule_         |     | - Input: paa_zone, exposure,  |    |
|  |   compliance()         |     |   pci_flag, data_class,       |    |
|  | - Full rule validation |     |   criticality                 |    |
|  | - Naming + G2G check   |     | - Output: recommended SZ     |    |
|  | - Returns: RuleCompli- |     |   code based on decision tree |    |
|  |   ance object          |     |                               |    |
|  +------------------------+     +-------------------------------+    |
|                                                                      |
|  +--------------------------------------------------------------+    |
|  | NAMING STANDARDS REFERENCE                                   |    |
|  +--------------------------------------------------------------+    |
|  |                                                              |    |
|  | get_naming_standards_info() -> NamingStandardsInfo           |    |
|  |   - prefixes: {group: "grp-", server: "svr-",               |    |
|  |               subnet: "rng-"}                                |    |
|  |   - valid_nh_ids: ["NH01"..."NH17"]                          |    |
|  |   - valid_sz_codes: ["CDE","GEN","DMZ","RST","MGT",...]     |    |
|  |   - valid_subtypes: ["WEB","APP","DB","BATCH","MQ",...]      |    |
|  |   - format_templates:                                        |    |
|  |     - group: "grp-{AppID}-{NH}-{SZ}-{Subtype}"              |    |
|  |     - server: "svr-{AppID}-{NH}-{SZ}-{ServerName}"           |    |
|  |     - subnet: "rng-{AppID}-{NH}-{SZ}-{Descriptor}"           |    |
|  |   - enforcement_rules:                                       |    |
|  |     - group_to_group_required: true                          |    |
|  |     - exception_approval_required: true                      |    |
|  |     - naming_validation_strict: true                         |    |
|  +--------------------------------------------------------------+    |
+----------------------------------------------------------------------+
```

### Naming Standards Patterns

| Type | Prefix | Pattern | Example |
|------|--------|---------|---------|
| **Group** | `grp-` | `grp-{AppID}-{NH}-{SZ}-{Subtype}` | `grp-APP001-NH01-CDE-WEB` |
| **Server** | `svr-` | `svr-{AppID}-{NH}-{SZ}-{ServerName}` | `svr-APP001-NH05-GEN-DBPROD01` |
| **Subnet** | `rng-` | `rng-{AppID}-{NH}-{SZ}-{Descriptor}` | `rng-APP001-NH12-DMZ-WEBSUBNET` |

### Valid Subtypes

| Subtype | Description |
|---------|-------------|
| `WEB` | Web servers |
| `APP` | Application servers |
| `DB` | Database servers |
| `BATCH` | Batch processing servers |
| `MQ` | Message queue servers |
| `CACHE` | Cache servers |
| `LB` | Load balancers |
| `PROXY` | Proxy servers |
| `MON` | Monitoring servers |
| `LOG` | Logging servers |
| `DNS` | DNS servers |
| `NTP` | NTP servers |
| `SMTP` | SMTP servers |
| `FTP` | FTP servers |
| `API` | API gateway servers |

---

## 8. Level 4: Code Diagram - NGDC Data Model

### Description

The NGDC Data Model shows the structure of the modernized data center constructs used throughout the application.

### Data Model Diagram

```
+----------------------------------------------------------------------+
|                      NGDC DATA MODEL                                 |
|                      (app/database.py)                               |
+----------------------------------------------------------------------+
|                                                                      |
|  +---------------------------+    +------------------------------+   |
|  | NEIGHBOURHOODS_REGISTRY   |    | SECURITY_ZONES               |   |
|  +---------------------------+    +------------------------------+   |
|  | id: str (NH01-NH17)       |    | code: str                    |   |
|  | name: str                 |    | name: str                    |   |
|  | zone: str                 |    | description: str             |   |
|  | environment: str          |    | risk_level: str              |   |
|  | description: str          |    | compliance: list[str]        |   |
|  | data_center: str          |    +------------------------------+   |
|  | status: str               |                                      |
|  +---------------------------+    +------------------------------+   |
|                                   | NGDC_DATA_CENTERS            |   |
|  +---------------------------+    +------------------------------+   |
|  | APPLICATIONS              |    | id: str                      |   |
|  +---------------------------+    | name: str                    |   |
|  | id: str                   |    | location: str                |   |
|  | name: str                 |    | status: str                  |   |
|  | app_id: str               |    | neighbourhoods: list[str]    |   |
|  | owner: str                |    | ip_groups: list[IPGroup]     |   |
|  | nh: str                   |    +------------------------------+   |
|  | sz: str                   |                                      |
|  | criticality: str          |    +------------------------------+   |
|  | pci_compliant: bool       |    | LEGACY_DATA_CENTERS          |   |
|  +---------------------------+    +------------------------------+   |
|                                   | id: str                      |   |
|  +---------------------------+    | name: str                    |   |
|  | FIREWALL_RULES            |    | location: str                |   |
|  +---------------------------+    | status: str                  |   |
|  | id: str                   |    | migration_target: str        |   |
|  | name: str                 |    | ip_ranges: list[str]         |   |
|  | source: str               |    +------------------------------+   |
|  | destination: str          |                                      |
|  | port: str                 |    +------------------------------+   |
|  | protocol: str             |    | NAMING_STANDARDS             |   |
|  | action: str               |    +------------------------------+   |
|  | status: str               |    | prefixes: dict               |   |
|  | application_name: str     |    | valid_nh_ids: list[str]      |   |
|  | compliance:               |    | valid_sz_codes: list[str]    |   |
|  |   naming_valid: bool      |    | valid_subtypes: list[str]    |   |
|  |   naming_errors: list     |    | format_templates: dict       |   |
|  |   group_to_group: bool    |    | enforcement_rules: dict      |   |
|  |   requires_exception: bool|    +------------------------------+   |
|  | created_at: str           |                                      |
|  | updated_at: str           |                                      |
|  | history: list[HistoryEntry]|                                     |
|  +---------------------------+                                      |
+----------------------------------------------------------------------+
```

### Neighbourhood Registry (NH01-NH17)

| ID | Name | Zone | Environment |
|----|------|------|-------------|
| NH01 | Technology Enablement Services | General | Production |
| NH02 | Customer Facing Applications | DMZ | Production |
| NH03 | Internal Business Applications | General | Production |
| NH04 | Data Analytics & Warehousing | General | Production |
| NH05 | Database Services | Restricted | Production |
| NH06 | Middleware & Integration | General | Production |
| NH07 | Security Services | Restricted | Production |
| NH08 | Network Management | Management | Production |
| NH09 | Storage & Backup | Restricted | Production |
| NH10 | Development & Testing | General | Non-Production |
| NH11 | Staging & UAT | General | Non-Production |
| NH12 | DMZ External Services | DMZ | Production |
| NH13 | PCI Cardholder Data Env | CDE | Production |
| NH14 | Legacy Integration | General | Production |
| NH15 | Cloud Connectivity | DMZ | Production |
| NH16 | Disaster Recovery | General | DR |
| NH17 | Pre-Production DMZ | DMZ | Non-Production |

### Security Zones (17 Zones)

| Code | Name | Risk Level |
|------|------|------------|
| CDE | Cardholder Data Environment | Critical |
| GEN | General Zone | Standard |
| DMZ | Demilitarized Zone | High |
| RST | Restricted Zone | High |
| MGT | Management Zone | High |
| PNA | PCI Network Access | Critical |
| EPAA | External PAA | High |
| UCPA | UC Payment Area | Critical |
| BCCI | BCC Internal | Standard |
| GGEN | Global General | Standard |
| EPIN | External PIN | Critical |
| LPAA | Local PAA | High |
| USPP | US Payment Processing | Critical |
| EXEN | External Enterprise | High |
| SPN | Secure Private Network | High |
| CPN | Corporate Private Network | Standard |
| EXT | External | High |

---

## 9. Deployment Architecture

### Diagram

```
+----------------------------------------------------------------------+
|                    DEPLOYMENT ARCHITECTURE                            |
+----------------------------------------------------------------------+
|                                                                      |
|  +------- PRODUCTION ENVIRONMENT -----------------------------------+|
|  |                                                                  ||
|  |  +------------------+       +------------------+                 ||
|  |  |  CDN / WAF       |       |  Load Balancer   |                 ||
|  |  |  (CloudFlare)    +------>+  (L7 Routing)    |                 ||
|  |  +------------------+       +--------+---------+                 ||
|  |                                      |                           ||
|  |                     +----------------+----------------+          ||
|  |                     |                                 |          ||
|  |              +------v------+                  +-------v-----+   ||
|  |              |  Frontend   |                  |  Backend     |   ||
|  |              |  Container  |                  |  Container   |   ||
|  |              |             |                  |              |   ||
|  |              |  React SPA  |    REST API      |  FastAPI     |   ||
|  |              |  (Nginx)    +----------------->+  (Uvicorn)   |   ||
|  |              |  Port: 80   |                  |  Port: 8000  |   ||
|  |              +-------------+                  +------+-------+   ||
|  |                                                      |           ||
|  |                                               +------v-------+  ||
|  |                                               |  Database    |  ||
|  |                                               |  PostgreSQL  |  ||
|  |                                               |  Port: 5432  |  ||
|  |                                               +--------------+  ||
|  +------------------------------------------------------------------+|
|                                                                      |
|  +------- DEVELOPMENT ENVIRONMENT -----------------------------------+|
|  |                                                                  ||
|  |  +------------------+                  +------------------+      ||
|  |  |  Vite Dev Server |    REST API      |  Uvicorn Dev     |      ||
|  |  |  Port: 5173      +----------------->+  Port: 8000      |      ||
|  |  +------------------+                  +------------------+      ||
|  |                                               |                  ||
|  |                                        +------v-------+         ||
|  |                                        | In-Memory DB |         ||
|  |                                        | (Python Dict)|         ||
|  |                                        +--------------+         ||
|  +------------------------------------------------------------------+|
+----------------------------------------------------------------------+
```

### Environment Configuration

| Environment | Frontend | Backend | Database | CDN |
|-------------|----------|---------|----------|-----|
| **Development** | Vite Dev Server (localhost:5173) | Uvicorn (localhost:8000) | In-Memory (Python Dict) | N/A |
| **Staging** | Nginx Container | Uvicorn Container | PostgreSQL | CloudFlare |
| **Production** | Nginx Container (HA) | Uvicorn Container (HA) | PostgreSQL (HA + Replication) | CloudFlare |

---

## 10. Security Architecture

### Authentication & Authorization

```
+----------------------------------------------------------------------+
|                    SECURITY ARCHITECTURE                             |
+----------------------------------------------------------------------+
|                                                                      |
|  +------ AUTHENTICATION LAYER ------------------------------------+ |
|  |                                                                | |
|  |  User Request                                                  | |
|  |      |                                                         | |
|  |      v                                                         | |
|  |  +------------------+     +------------------+                 | |
|  |  | WAF / Rate Limit |---->| SAML SSO / LDAP  |                 | |
|  |  | (DDoS Protection)|     | Authentication   |                 | |
|  |  +------------------+     +--------+---------+                 | |
|  |                                    |                           | |
|  |                           +--------v---------+                 | |
|  |                           | JWT Token Issue   |                 | |
|  |                           | (Bearer Token)    |                 | |
|  |                           +--------+---------+                 | |
|  |                                    |                           | |
|  +------------------------------------+---------------------------+ |
|                                       |                             |
|  +------ AUTHORIZATION LAYER ---------v---------------------------+ |
|  |                                                                | |
|  |  +------------------+     +------------------+                 | |
|  |  | Role-Based       |     | Policy Engine    |                 | |
|  |  | Access Control   |     | (NGDC Matrix)    |                 | |
|  |  |                  |     |                  |                 | |
|  |  | - Admin          |     | - NH access      |                 | |
|  |  | - Engineer       |     | - SZ permissions |                 | |
|  |  | - Analyst        |     | - Rule scopes    |                 | |
|  |  | - Viewer         |     | - App ownership  |                 | |
|  |  +------------------+     +------------------+                 | |
|  +----------------------------------------------------------------+ |
|                                                                      |
|  +------ DATA PROTECTION LAYER -----------------------------------+ |
|  |                                                                | |
|  |  - TLS 1.3 for all communications                             | |
|  |  - AES-256 encryption at rest                                 | |
|  |  - Audit logging for all rule changes                         | |
|  |  - Naming standards prevent IP exposure                       | |
|  |  - Group-to-group enforcement reduces attack surface          | |
|  +----------------------------------------------------------------+ |
+----------------------------------------------------------------------+
```

### Security Roles

| Role | Permissions |
|------|------------|
| **Admin** | Full system access, configuration management, user management |
| **Network Engineer** | Create/modify rules, submit CHG requests, execute migrations |
| **Security Analyst** | Review rules, certify rules, approve exceptions, audit trail access |
| **Viewer** | Read-only access to rules, reports, and dashboards |

---

## 11. Data Flow Architecture

### Rule Creation Flow

```
User Input --> SourcePanel --> Naming Standards Engine --> Validation
                                                              |
                                                    [Valid?]--+--[Invalid]
                                                      |              |
                                                      v              v
                                              DestinationPanel   Error Display
                                                      |          (Red badges)
                                                      v
                                              PolicyFlowCanvas
                                                      |
                                                      v
                                              Rule Lifecycle Table
                                                      |
                                              [Status: Draft]
                                                      |
                                              Submit for Review
                                                      |
                                              [Status: Pending Review]
                                                      |
                                              Certify / Approve
                                                      |
                                              [Status: Certified]
                                                      |
                                              Submit CHG Request
                                                      |
                                              ServiceNow Integration
                                                      |
                                              [Status: Deployed]
```

### Migration Flow

```
Legacy DC Rules --> Import/Select --> Validation Engine
                                          |
                                   [Standards Check]
                                          |
                              +-----------+-----------+
                              |                       |
                         [Compliant]            [Non-Compliant]
                              |                       |
                              v                       v
                        Direct Map            Naming Suggestion
                              |                       |
                              |                 [User Accepts?]
                              |                   |         |
                              |                  Yes        No
                              |                   |         |
                              |                   v         v
                              |            Apply Suggestion  Manual Edit
                              |                   |         |
                              +---+---+-----------+---------+
                                  |
                            NH/SZ Assignment
                                  |
                            NGDC Mapping
                                  |
                            Migration Plan
                                  |
                            Execute Migration
                                  |
                            New NGDC Rules Created
```

---

## 12. Appendix

### A. Technology Stack Summary

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Frontend Framework | React | 18.x | UI component framework |
| Frontend Language | TypeScript | 5.x | Type-safe JavaScript |
| Build Tool | Vite | 6.x | Fast build and HMR |
| CSS Framework | Tailwind CSS | 3.x | Utility-first styling |
| UI Components | shadcn/ui | Latest | Pre-built accessible components |
| Backend Framework | FastAPI | 0.115.x | High-performance Python API |
| Backend Language | Python | 3.12 | Server-side logic |
| Package Manager | Poetry | 1.x | Python dependency management |
| ASGI Server | Uvicorn | 0.34.x | Production ASGI server |
| Icons | Lucide React | Latest | Icon library |

### B. API Endpoint Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/firewall-rules` | List all firewall rules |
| POST | `/api/firewall-rules` | Create a new firewall rule |
| PUT | `/api/firewall-rules/{id}` | Update a firewall rule |
| DELETE | `/api/firewall-rules/{id}` | Delete a firewall rule |
| POST | `/api/firewall-rules/{id}/certify` | Certify a firewall rule |
| POST | `/api/firewall-rules/{id}/submit-chg` | Submit CHG request |
| GET | `/api/firewall-rules/{id}/history` | Get rule history |
| GET | `/api/migration/legacy-rules` | Get legacy firewall rules |
| POST | `/api/migration/validate` | Validate migration mapping |
| POST | `/api/migration/map` | Create migration mapping |
| POST | `/api/migration/execute` | Execute migration |
| GET | `/api/reference/neighbourhoods` | Get all NGDC neighbourhoods |
| GET | `/api/reference/security-zones` | Get all security zones |
| GET | `/api/reference/applications` | Get all applications |
| GET | `/api/reference/naming-standards` | Get naming standards info |
| POST | `/api/reference/naming-standards/validate` | Validate a name |
| POST | `/api/reference/naming-standards/generate` | Generate compliant name |
| POST | `/api/reference/naming-standards/suggest` | Suggest compliant name |
| POST | `/api/reference/naming-standards/determine-zone` | Determine security zone |

### C. Glossary

| Term | Definition |
|------|-----------|
| **NGDC** | Next-Generation Data Center - Modernized infrastructure with neighbourhood-based segmentation |
| **NH** | Neighbourhood - A logical grouping within NGDC (NH01-NH17) |
| **SZ** | Security Zone - A security classification within a neighbourhood |
| **Birthright** | Default firewall rules automatically applied based on NH/SZ membership |
| **CHG** | Change Request - ServiceNow change management ticket |
| **G2G** | Group-to-Group - Policy requiring rules to reference groups rather than individual IPs |
| **CDE** | Cardholder Data Environment - PCI DSS compliant zone |
| **DMZ** | Demilitarized Zone - Network segment between internal and external networks |
| **PAA** | Payment Application Area - Zone for payment processing applications |
| **C4 Model** | Context, Container, Component, Code - Software architecture documentation model |
| **GitOps** | Git-based operations - Using Git as single source of truth for infrastructure |

---

*This document follows the C4 model architecture standard and is maintained as part of the Network Firewall Studio documentation suite.*
