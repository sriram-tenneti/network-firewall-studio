import { describe, expect, it } from "vitest";
import { transformRule } from "../../src/lib/api";

const baseRaw = {
  rule_id: "R-1001",
  rule_name: "crm-to-db",
  application: "CRM",
  environment: "Production",
  datacenter: "ALPHA_NGDC",
  source: "grp-CRM-NH02-PAA",
  destination: "grp-DB-NH02-DAA",
  source_zone: "NH02-PAA",
  destination_zone: "NH02-DAA",
  port: "1521",
  protocol: "tcp",
  status: "Draft",
};

describe("transformRule", () => {
  it("maps a group-to-group rule and flags compliance correctly", () => {
    const out = transformRule(baseRaw as any);
    expect(out.rule_id).toBe("R-1001");
    expect(out.status).toBe("Draft");
    expect(out.source.group_name).toBe("grp-CRM-NH02-PAA");
    expect(out.source.source_type).toBe("Group");
    expect(out.destination.name).toBe("grp-DB-NH02-DAA");
    expect(out.compliance.naming_valid).toBe(true);
    expect(out.compliance.group_to_group).toBe(true);
    expect(out.compliance.requires_exception).toBe(false);
  });

  it("flags requires_exception when source is a host (svr-)", () => {
    const out = transformRule({
      ...baseRaw,
      source: "svr-10.10.10.10",
    } as any);
    expect(out.compliance.naming_valid).toBe(true);
    expect(out.compliance.group_to_group).toBe(false);
    expect(out.compliance.requires_exception).toBe(true);
  });

  it("treats legacy g- prefixed source as a group", () => {
    const out = transformRule({
      ...baseRaw,
      source: "g-LegacyApp",
    } as any);
    expect(out.compliance.group_to_group).toBe(true);
  });

  it("preserves status across lifecycle states", () => {
    for (const status of ["Draft", "Submitted", "Approved", "Deployed"]) {
      const out = transformRule({ ...baseRaw, status } as any);
      expect(out.status).toBe(status);
    }
  });
});
