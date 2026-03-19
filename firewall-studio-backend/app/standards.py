"""Policy matrices and compliance standards for firewall rule validation.

This module contains the NGDC Data Center Matrix - the birthright rules
that determine whether traffic between zones is permitted or blocked by default.

Matrices:
- NGDC Prod Rules: DC/NH/SZ matching with Same/Different/Any logic
- Non-Prod / Pre-Prod Rules: Source Non-Prod zone to Destination Pre-Prod zone mapping
- Heritage DC Matrix: Legacy-to-NGDC migration rules

Where the matrix says "Blocked" = Firewall rule request must be submitted.
Where the matrix says "Permitted" = Traffic flows by default, no request needed.

All matrices are editable via the Admin UI.
"""


# =====================================================================
# NGDC PROD RULES
# Uses DC/NH/SZ matching: Same, Different, Any
# Exact reproduction of the NGDC Data Center Matrix reference
# =====================================================================
NGDC_PROD_MATRIX: list[dict[str, str]] = [
    # Row 1: Any DC, Any NH, GEN -> GEN = Permitted
    {"src_dc": "Any", "dst_dc": "Any", "src_nh": "Any", "dst_nh": "Any",
     "src_sz": "GEN", "dst_sz": "GEN", "action": "Permitted",
     "matrix_type": "NGDC Prod",
     "reason": "GEN-to-GEN traffic is always permitted across all DCs and NHs"},

    # Row 2: Same DC, Same NH, Same SZ = Permitted
    {"src_dc": "Same", "dst_dc": "Same", "src_nh": "Same", "dst_nh": "Same",
     "src_sz": "Same", "dst_sz": "Same", "action": "Permitted",
     "matrix_type": "NGDC Prod",
     "reason": "Same DC + Same NH + Same SZ = Permitted (intra-zone traffic)"},

    # Row 3: Different DC, Same NH, Same SZ = Permitted
    {"src_dc": "Different", "dst_dc": "Different", "src_nh": "Same", "dst_nh": "Same",
     "src_sz": "Same", "dst_sz": "Same", "action": "Permitted",
     "matrix_type": "NGDC Prod",
     "reason": "Different DC + Same NH + Same SZ = Permitted (cross-DC same zone)"},

    # Row 4: Same DC, Same NH, Different SZ = Blocked
    {"src_dc": "Same", "dst_dc": "Same", "src_nh": "Same", "dst_nh": "Same",
     "src_sz": "Different", "dst_sz": "Different", "action": "Blocked",
     "matrix_type": "NGDC Prod",
     "reason": "Same DC + Same NH + Different SZ = Blocked; firewall rule request required"},

    # Row 5: Same DC, Different NH, Same SZ = Permitted
    {"src_dc": "Same", "dst_dc": "Same", "src_nh": "Different", "dst_nh": "Different",
     "src_sz": "Same", "dst_sz": "Same", "action": "Permitted",
     "matrix_type": "NGDC Prod",
     "reason": "Same DC + Different NH + Same SZ = Permitted (cross-NH same zone)"},

    # Row 6: Different DC, Different NH, Same SZ = Blocked
    {"src_dc": "Different", "dst_dc": "Different", "src_nh": "Different", "dst_nh": "Different",
     "src_sz": "Same", "dst_sz": "Same", "action": "Blocked",
     "matrix_type": "NGDC Prod",
     "reason": "Different DC + Different NH + Same SZ = Blocked; firewall rule request required"},

    # Row 7: Same DC, Non-Prod to PROD, Any SZ = Blocked
    {"src_dc": "Same", "dst_dc": "Same", "src_nh": "Non-Prod", "dst_nh": "Prod",
     "src_sz": "Any", "dst_sz": "Any", "action": "Blocked",
     "matrix_type": "NGDC Prod",
     "reason": "Cross-environment (Non-Prod to Prod) traffic is always blocked; firewall rule request required"},
]


# =====================================================================
# NON-PROD / PRE-PROD RULES
# Source: Non-Prod zones | Destination: Pre-Prod zones
# DC is always "Any" for non-prod rules
# Blocked = Firewall rule request required
# =====================================================================
NONPROD_PREPROD_MATRIX: list[dict[str, str]] = [
    # Non-Prod UGEN/USTD -> Pre-Prod UGEN/USTD = Permitted
    {"src_dc": "Any", "source_zone": "UGEN", "dest_zone": "UGEN",
     "action": "Permitted", "matrix_type": "Non-Prod / Pre-Prod",
     "reason": "Non-Prod UGEN/USTD to Pre-Prod UGEN/USTD = Permitted"},
    {"src_dc": "Any", "source_zone": "USTD", "dest_zone": "USTD",
     "action": "Permitted", "matrix_type": "Non-Prod / Pre-Prod",
     "reason": "Non-Prod UGEN/USTD to Pre-Prod UGEN/USTD = Permitted"},
    {"src_dc": "Any", "source_zone": "UGEN", "dest_zone": "USTD",
     "action": "Permitted", "matrix_type": "Non-Prod / Pre-Prod",
     "reason": "Non-Prod UGEN/USTD to Pre-Prod UGEN/USTD = Permitted"},
    {"src_dc": "Any", "source_zone": "USTD", "dest_zone": "UGEN",
     "action": "Permitted", "matrix_type": "Non-Prod / Pre-Prod",
     "reason": "Non-Prod UGEN/USTD to Pre-Prod UGEN/USTD = Permitted"},

    # Non-Prod UGEN/USTD -> Pre-Prod PAA/CCS/CPA = Blocked
    {"src_dc": "Any", "source_zone": "UGEN", "dest_zone": "PAA",
     "action": "Blocked", "matrix_type": "Non-Prod / Pre-Prod",
     "reason": "Non-Prod UGEN/USTD to Pre-Prod PAA/CCS/CPA = Blocked; firewall rule request required"},
    {"src_dc": "Any", "source_zone": "UGEN", "dest_zone": "CCS",
     "action": "Blocked", "matrix_type": "Non-Prod / Pre-Prod",
     "reason": "Non-Prod UGEN/USTD to Pre-Prod PAA/CCS/CPA = Blocked; firewall rule request required"},
    {"src_dc": "Any", "source_zone": "UGEN", "dest_zone": "CPA",
     "action": "Blocked", "matrix_type": "Non-Prod / Pre-Prod",
     "reason": "Non-Prod UGEN/USTD to Pre-Prod PAA/CCS/CPA = Blocked; firewall rule request required"},
    {"src_dc": "Any", "source_zone": "USTD", "dest_zone": "PAA",
     "action": "Blocked", "matrix_type": "Non-Prod / Pre-Prod",
     "reason": "Non-Prod UGEN/USTD to Pre-Prod PAA/CCS/CPA = Blocked; firewall rule request required"},
    {"src_dc": "Any", "source_zone": "USTD", "dest_zone": "CCS",
     "action": "Blocked", "matrix_type": "Non-Prod / Pre-Prod",
     "reason": "Non-Prod UGEN/USTD to Pre-Prod PAA/CCS/CPA = Blocked; firewall rule request required"},
    {"src_dc": "Any", "source_zone": "USTD", "dest_zone": "CPA",
     "action": "Blocked", "matrix_type": "Non-Prod / Pre-Prod",
     "reason": "Non-Prod UGEN/USTD to Pre-Prod PAA/CCS/CPA = Blocked; firewall rule request required"},

    # Non-Prod UCCS -> Pre-Prod PAA/CCS/CPA = Blocked
    {"src_dc": "Any", "source_zone": "UCCS", "dest_zone": "PAA",
     "action": "Blocked", "matrix_type": "Non-Prod / Pre-Prod",
     "reason": "Non-Prod UCCS to Pre-Prod PAA/CCS/CPA = Blocked; firewall rule request required"},
    {"src_dc": "Any", "source_zone": "UCCS", "dest_zone": "CCS",
     "action": "Blocked", "matrix_type": "Non-Prod / Pre-Prod",
     "reason": "Non-Prod UCCS to Pre-Prod PAA/CCS/CPA = Blocked; firewall rule request required"},
    {"src_dc": "Any", "source_zone": "UCCS", "dest_zone": "CPA",
     "action": "Blocked", "matrix_type": "Non-Prod / Pre-Prod",
     "reason": "Non-Prod UCCS to Pre-Prod PAA/CCS/CPA = Blocked; firewall rule request required"},

    # Non-Prod UPAA -> Pre-Prod PAA/CCS/CPA = Blocked
    {"src_dc": "Any", "source_zone": "UPAA", "dest_zone": "PAA",
     "action": "Blocked", "matrix_type": "Non-Prod / Pre-Prod",
     "reason": "Non-Prod UPAA to Pre-Prod PAA/CCS/CPA = Blocked; firewall rule request required"},
    {"src_dc": "Any", "source_zone": "UPAA", "dest_zone": "CCS",
     "action": "Blocked", "matrix_type": "Non-Prod / Pre-Prod",
     "reason": "Non-Prod UPAA to Pre-Prod PAA/CCS/CPA = Blocked; firewall rule request required"},
    {"src_dc": "Any", "source_zone": "UPAA", "dest_zone": "CPA",
     "action": "Blocked", "matrix_type": "Non-Prod / Pre-Prod",
     "reason": "Non-Prod UPAA to Pre-Prod PAA/CCS/CPA = Blocked; firewall rule request required"},

    # Non-Prod UCPA -> Pre-Prod PAA/CCS/CPA = Blocked
    {"src_dc": "Any", "source_zone": "UCPA", "dest_zone": "PAA",
     "action": "Blocked", "matrix_type": "Non-Prod / Pre-Prod",
     "reason": "Non-Prod UCPA to Pre-Prod PAA/CCS/CPA = Blocked; firewall rule request required"},
    {"src_dc": "Any", "source_zone": "UCPA", "dest_zone": "CCS",
     "action": "Blocked", "matrix_type": "Non-Prod / Pre-Prod",
     "reason": "Non-Prod UCPA to Pre-Prod PAA/CCS/CPA = Blocked; firewall rule request required"},
    {"src_dc": "Any", "source_zone": "UCPA", "dest_zone": "CPA",
     "action": "Blocked", "matrix_type": "Non-Prod / Pre-Prod",
     "reason": "Non-Prod UCPA to Pre-Prod PAA/CCS/CPA = Blocked; firewall rule request required"},

    # Non-Prod UCDE -> Pre-Prod PAA/CCS/CPA = Blocked
    {"src_dc": "Any", "source_zone": "UCDE", "dest_zone": "PAA",
     "action": "Blocked", "matrix_type": "Non-Prod / Pre-Prod",
     "reason": "Non-Prod UCDE to Pre-Prod PAA/CCS/CPA = Blocked; firewall rule request required"},
    {"src_dc": "Any", "source_zone": "UCDE", "dest_zone": "CCS",
     "action": "Blocked", "matrix_type": "Non-Prod / Pre-Prod",
     "reason": "Non-Prod UCDE to Pre-Prod PAA/CCS/CPA = Blocked; firewall rule request required"},
    {"src_dc": "Any", "source_zone": "UCDE", "dest_zone": "CPA",
     "action": "Blocked", "matrix_type": "Non-Prod / Pre-Prod",
     "reason": "Non-Prod UCDE to Pre-Prod PAA/CCS/CPA = Blocked; firewall rule request required"},
]


# =====================================================================
# HERITAGE DC MATRIX
# Rules governing traffic from Legacy DC zones to NGDC zones
# Used during migration to determine what is permitted vs. blocked
# =====================================================================
HERITAGE_DC_MATRIX: list[dict[str, str]] = [
    {"source_zone": "GEN", "dest_zone": "GEN", "action": "Permitted",
     "matrix_type": "Heritage DC", "reason": "Heritage GEN to NGDC GEN = Permitted (same zone class)"},
    {"source_zone": "GEN", "dest_zone": "CDE", "action": "Blocked",
     "matrix_type": "Heritage DC", "reason": "Heritage GEN to NGDC CDE = Blocked; firewall rule request required"},
    {"source_zone": "GEN", "dest_zone": "CPA", "action": "Blocked",
     "matrix_type": "Heritage DC", "reason": "Heritage GEN to NGDC CPA = Blocked; firewall rule request required"},
    {"source_zone": "CDE", "dest_zone": "CDE", "action": "Permitted",
     "matrix_type": "Heritage DC", "reason": "Heritage CDE to NGDC CDE = Permitted (same zone class)"},
    {"source_zone": "CDE", "dest_zone": "GEN", "action": "Permitted",
     "matrix_type": "Heritage DC", "reason": "Heritage CDE to NGDC GEN = Permitted (less restrictive dest)"},
    {"source_zone": "CDE", "dest_zone": "CPA", "action": "Blocked",
     "matrix_type": "Heritage DC", "reason": "Heritage CDE to NGDC CPA = Blocked; firewall rule request required"},
    {"source_zone": "CPA", "dest_zone": "CPA", "action": "Permitted",
     "matrix_type": "Heritage DC", "reason": "Heritage CPA to NGDC CPA = Permitted (same zone class)"},
    {"source_zone": "CPA", "dest_zone": "GEN", "action": "Permitted",
     "matrix_type": "Heritage DC", "reason": "Heritage CPA to NGDC GEN = Permitted (less restrictive dest)"},
    {"source_zone": "CPA", "dest_zone": "CDE", "action": "Blocked",
     "matrix_type": "Heritage DC", "reason": "Heritage CPA to NGDC CDE = Blocked; firewall rule request required"},
    {"source_zone": "DMZ", "dest_zone": "GEN", "action": "Blocked",
     "matrix_type": "Heritage DC", "reason": "Heritage DMZ to NGDC GEN = Blocked; firewall rule request required"},
    {"source_zone": "DMZ", "dest_zone": "CDE", "action": "Blocked",
     "matrix_type": "Heritage DC", "reason": "Heritage DMZ to NGDC CDE = Blocked; firewall rule request required"},
    {"source_zone": "DMZ", "dest_zone": "DMZ", "action": "Permitted",
     "matrix_type": "Heritage DC", "reason": "Heritage DMZ to NGDC DMZ = Permitted (same zone class)"},
    {"source_zone": "RST", "dest_zone": "RST", "action": "Permitted",
     "matrix_type": "Heritage DC", "reason": "Heritage RST to NGDC RST = Permitted (same zone class)"},
    {"source_zone": "RST", "dest_zone": "GEN", "action": "Permitted",
     "matrix_type": "Heritage DC", "reason": "Heritage RST to NGDC GEN = Permitted (less restrictive dest)"},
    {"source_zone": "RST", "dest_zone": "CDE", "action": "Blocked",
     "matrix_type": "Heritage DC", "reason": "Heritage RST to NGDC CDE = Blocked; firewall rule request required"},
    {"source_zone": "PSE", "dest_zone": "PSE", "action": "Permitted",
     "matrix_type": "Heritage DC", "reason": "Heritage PSE to NGDC PSE = Permitted (same zone class)"},
    {"source_zone": "PSE", "dest_zone": "GEN", "action": "Blocked",
     "matrix_type": "Heritage DC", "reason": "Heritage PSE to NGDC GEN = Blocked; firewall rule request required"},
    {"source_zone": "3PY", "dest_zone": "3PY", "action": "Permitted",
     "matrix_type": "Heritage DC", "reason": "Heritage 3PY to NGDC 3PY = Permitted (same zone class)"},
    {"source_zone": "3PY", "dest_zone": "GEN", "action": "Blocked",
     "matrix_type": "Heritage DC", "reason": "Heritage 3PY to NGDC GEN = Blocked; firewall rule request required"},
    {"source_zone": "CAN", "dest_zone": "CAN", "action": "Permitted",
     "matrix_type": "Heritage DC", "reason": "Heritage CAN to NGDC CAN = Permitted (same zone class)"},
    {"source_zone": "CAN", "dest_zone": "GEN", "action": "Blocked",
     "matrix_type": "Heritage DC", "reason": "Heritage CAN to NGDC GEN = Blocked; firewall rule request required"},
    {"source_zone": "CAN", "dest_zone": "3PY", "action": "Blocked",
     "matrix_type": "Heritage DC", "reason": "Heritage CAN to NGDC 3PY = Blocked; firewall rule request required"},
]


# =====================================================================
# COMBINED POLICY MATRIX (for quick lookup)
# =====================================================================
POLICY_MATRIX: list[dict[str, str]] = (
    HERITAGE_DC_MATRIX + NONPROD_PREPROD_MATRIX
)
