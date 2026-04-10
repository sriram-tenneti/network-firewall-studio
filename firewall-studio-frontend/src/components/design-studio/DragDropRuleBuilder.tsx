import { useState, useEffect, useMemo, useCallback } from 'react';
import type { Application, BirthrightValidation, NeighbourhoodRegistry, SecurityZone, NGDCDataCenter, FirewallGroup, FirewallRule } from '@/types';
import * as api from '@/lib/api';
import { autoPrefix, isNgdcGroupName } from '@/lib/utils';

interface DragDropRuleBuilderProps {
  applications: Application[];
  onRuleCreated: () => void;
  editRule?: FirewallRule | null;
  onEditComplete?: () => void;
}

// Fallback static data (used while API data loads)
const FALLBACK_NEIGHBOURHOODS = [
  { id: 'NH01', name: 'Technology Enablement Services' },
  { id: 'NH02', name: 'Core Banking' },
  { id: 'NH03', name: 'Digital Channels' },
  { id: 'NH04', name: 'Wealth Management' },
  { id: 'NH05', name: 'Enterprise Services' },
  { id: 'NH06', name: 'Wholesale Banking' },
  { id: 'NH07', name: 'Global Payments and Liquidity' },
  { id: 'NH08', name: 'Data and Analytics' },
  { id: 'NH09', name: 'Assisted Channels' },
  { id: 'NH10', name: 'Consumer Lending' },
  { id: 'NH11', name: 'Production Mainframe' },
  { id: 'NH12', name: 'Non-Production Mainframe' },
  { id: 'NH13', name: 'Non-Production Shared' },
  { id: 'NH14', name: 'DMZ' },
  { id: 'NH15', name: 'Non-Production DMZ' },
  { id: 'NH16', name: 'Pre-Production (Non-Prod Shared)' },
  { id: 'NH17', name: 'Pre-Production DMZ' },
];

const FALLBACK_DATACENTERS = [
  { code: 'ALPHA_NGDC', name: 'Alpha NGDC' },
  { code: 'BETA_NGDC', name: 'Beta NGDC' },
  { code: 'GAMMA_NGDC', name: 'Gamma NGDC' },
];

const SUBTYPES = [
  { code: 'APP', name: 'Application Servers' },
  { code: 'WEB', name: 'Web Servers' },
  { code: 'DB', name: 'Database Servers' },
  { code: 'BAT', name: 'Batch Servers' },
  { code: 'MQ', name: 'Message Queue' },
  { code: 'API', name: 'API Servers' },
  { code: 'LB', name: 'Load Balancers' },
  { code: 'MON', name: 'Monitoring' },
  { code: 'MFR', name: 'Mainframe' },
  { code: 'SVC', name: 'Services' },
];

const PROTOCOLS = ['TCP', 'UDP', 'ICMP', 'ANY'];

const COMMON_PORTS = [
  { value: '443', label: 'HTTPS (443)' },
  { value: '80', label: 'HTTP (80)' },
  { value: '8443', label: 'Alt HTTPS (8443)' },
  { value: '8080', label: 'Alt HTTP (8080)' },
  { value: '1433', label: 'MSSQL (1433)' },
  { value: '1521', label: 'Oracle (1521)' },
  { value: '3306', label: 'MySQL (3306)' },
  { value: '5432', label: 'PostgreSQL (5432)' },
  { value: '1414', label: 'MQ (1414)' },
  { value: '9092', label: 'Kafka (9092)' },
  { value: '22', label: 'SSH (22)' },
  { value: '3389', label: 'RDP (3389)' },
];

export function DragDropRuleBuilder({ applications, onRuleCreated, editRule, onEditComplete }: DragDropRuleBuilderProps) {
  const isEditMode = !!editRule;
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [draftCreatedMsg, setDraftCreatedMsg] = useState('');

  const buildDefaultForm = () => ({
    application: '', dst_application: '', environment: 'Production', datacenter: '',
    src_component: '', dst_component: '',
    src_dc: '', dst_dc: '',
    src_nh: '', src_sz: '', src_subtype: 'APP', src_custom: '',
    dst_nh: '', dst_sz: '', dst_subtype: 'APP', dst_custom: '',
    port: '443', customPort: '', protocol: 'TCP', action: 'Allow', description: '',
  });

  // State for group auto-creation modal (source only)
  const [showCreateGroupModal, setShowCreateGroupModal] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');
  const [newGroupMembers, setNewGroupMembers] = useState<{type: string; value: string}[]>([]);
  const [creatingGroup, setCreatingGroup] = useState(false);
  // Wizard member-add row state
  const [wizMemberType, setWizMemberType] = useState<string>('ip');
  const [wizMemberValue, setWizMemberValue] = useState('');
  /** Whether the modal was opened for a destination group (vs source) */
  const [createGroupForDst, setCreateGroupForDst] = useState(false);

  const [form, setForm] = useState(buildDefaultForm);

  /** Try to extract the component code from an NGDC group name like grp-APP01-NH01-STD-WEB */
  const extractComponentFromGroup = (groupName: string): string => {
    if (!groupName) return '';
    const parts = groupName.split('-');
    // Pattern: grp-{app}-{nh}-{sz}-{component}
    if (parts.length >= 5 && parts[0].toLowerCase() === 'grp') {
      const candidate = parts[parts.length - 1].toUpperCase();
      const knownComponents = ['APP', 'WEB', 'DB', 'BAT', 'MQ', 'API', 'LB', 'MON', 'MFR', 'SVC'];
      if (knownComponents.includes(candidate)) return candidate;
    }
    return '';
  };

  // Pre-populate form when editing a draft rule
  useEffect(() => {
    if (!editRule) return;
    const src = editRule.source;
    const dst = editRule.destination;
    const srcGroup = (src?.group_name || src?.ip_address || src?.cidr || '') as string;
    // Destination group: could be stored as object {name, dest_ip, ...} or as plain string
    const dstGroup = typeof dst === 'string' ? dst : (dst?.name || dst?.dest_ip || '') as string;
    const srcSz = (src?.security_zone || '') as string;
    const srcNh = (src?.neighbourhood || '') as string;
    const ports = (src?.ports || (typeof dst === 'object' ? dst?.ports : '') || '') as string;
    // Access rule-level fields that were persisted during creation/update
    const ruleAny = editRule as unknown as Record<string, string>;
    const dstApp = ruleAny.dst_application || '';
    const dstNh = ruleAny.destination_nh || '';
    // Destination SZ: try rule-level destination_zone first, then from dst object
    const dstSz = ruleAny.destination_zone || (typeof dst === 'object' ? (dst?.security_zone || '') as string : '') as string;
    // Source NH: also check rule-level source_nh
    const resolvedSrcNh = srcNh || ruleAny.source_nh || '';
    // Extract component from stored field or from group name
    const srcComp = ruleAny.src_component || extractComponentFromGroup(srcGroup);
    const dstComp = ruleAny.dst_component || extractComponentFromGroup(dstGroup);
    setForm({
      application: editRule.application || '',
      dst_application: dstApp,
      environment: editRule.environment || 'Production',
      datacenter: editRule.datacenter || '',
      src_dc: (ruleAny.src_dc || editRule.datacenter || ''),
      dst_dc: (ruleAny.dst_dc || editRule.datacenter || ''),
      src_component: srcComp, dst_component: dstComp,
      src_nh: resolvedSrcNh, src_sz: srcSz, src_subtype: srcComp || 'APP', src_custom: srcGroup,
      dst_nh: dstNh, dst_sz: dstSz, dst_subtype: dstComp || 'APP', dst_custom: dstGroup,
      port: ports || '443', customPort: '', protocol: 'TCP',
      action: ruleAny.action || 'Allow',
      description: editRule.description || '',
    });
  }, [editRule]);
  const [birthrightResult, setBirthrightResult] = useState<BirthrightValidation | null>(null);
  const [validatingBR, setValidatingBR] = useState(false);

  // App DC Mappings for component-based NH/SZ filtering
  const [appDcMappings, setAppDcMappings] = useState<Record<string, unknown>[]>([]);

  // Load app DC mappings on mount
  useEffect(() => {
    api.getAppDCMappings()
      .then(m => setAppDcMappings(m))
      .catch(() => setAppDcMappings([]));
  }, []);

  // Helper: check if a mapping belongs to a given appId
  // The dropdown value is app_distributed_id (e.g. "APP01-NGDC"), but mappings may only
  // store app_id (e.g. "APP01"). Also resolve via the applications list.
  const mappingMatchesApp = useCallback((mr: Record<string, string>, appId: string): boolean => {
    if (!appId) return false;
    // Direct match on either field
    if (mr.app_distributed_id === appId || mr.app_id === appId) return true;
    // Resolve: if appId is an app_distributed_id, find the matching app_id from the applications list
    const appObj = applications.find(a => (a.app_distributed_id || a.app_id) === appId);
    if (appObj && mr.app_id === appObj.app_id) return true;
    return false;
  }, [applications]);

  // Derive available components for source app from app_dc_mappings
  const srcComponents = useMemo(() => {
    if (!form.application) return [] as string[];
    const comps = new Set<string>();
    for (const m of appDcMappings) {
      const mr = m as Record<string, string>;
      if (mappingMatchesApp(mr, form.application) && mr.component) {
        comps.add(mr.component);
      }
    }
    return Array.from(comps).sort();
  }, [form.application, appDcMappings, mappingMatchesApp]);

  // Derive available components for destination app
  const dstComponents = useMemo(() => {
    const dstApp = form.dst_application || form.application;
    if (!dstApp) return [] as string[];
    const comps = new Set<string>();
    for (const m of appDcMappings) {
      const mr = m as Record<string, string>;
      if (mappingMatchesApp(mr, dstApp) && mr.component) {
        comps.add(mr.component);
      }
    }
    return Array.from(comps).sort();
  }, [form.dst_application, form.application, appDcMappings, mappingMatchesApp]);

  // Source NH/SZ/DC from source app
  const [srcNHs, setSrcNHs] = useState<NeighbourhoodRegistry[]>([]);
  const [srcSZs, setSrcSZs] = useState<SecurityZone[]>([]);
  const [srcDCs, setSrcDCs] = useState<NGDCDataCenter[]>([]);
  const [loadingSrc, setLoadingSrc] = useState(false);

  // Destination NH/SZ/DC from destination app
  const [dstNHs, setDstNHs] = useState<NeighbourhoodRegistry[]>([]);
  const [dstSZs, setDstSZs] = useState<SecurityZone[]>([]);
  const [dstDCs, setDstDCs] = useState<NGDCDataCenter[]>([]);
  const [loadingDst, setLoadingDst] = useState(false);

  // NGDC groups for source and destination apps
  const [srcAppGroups, setSrcAppGroups] = useState<FirewallGroup[]>([]);
  const [dstAppGroups, setDstAppGroups] = useState<FirewallGroup[]>([]);

  // Load source app groups
  useEffect(() => {
    if (!form.application) { setSrcAppGroups([]); return; }
    api.getGroups(form.application)
      .then(groups => setSrcAppGroups(groups.filter(g => isNgdcGroupName(g.name))))
      .catch(() => setSrcAppGroups([]));
  }, [form.application]);

  // Load destination app groups
  useEffect(() => {
    const dstApp = form.dst_application || form.application;
    if (!dstApp) { setDstAppGroups([]); return; }
    api.getGroups(dstApp)
      .then(groups => setDstAppGroups(groups.filter(g => isNgdcGroupName(g.name))))
      .catch(() => setDstAppGroups([]));
  }, [form.dst_application, form.application]);

  const loadSrcData = useCallback(async (env: string, appId: string) => {
    if (!env) return;
    setLoadingSrc(true);
    try {
      const data = await api.getFilteredNhSzDc(env, appId || undefined);
      setSrcNHs(data.neighbourhoods || []);
      setSrcSZs(data.security_zones || []);
      setSrcDCs(data.datacenters || []);
    } catch {
      setSrcNHs([]); setSrcSZs([]); setSrcDCs([]);
    }
    setLoadingSrc(false);
  }, []);

  const loadDstData = useCallback(async (env: string, appId?: string) => {
    if (!env) return;
    setLoadingDst(true);
    try {
      const data = await api.getFilteredNhSzDc(env, appId);
      setDstNHs(data.neighbourhoods || []);
      setDstSZs(data.security_zones || []);
      setDstDCs(data.datacenters || []);
    } catch {
      setDstNHs([]); setDstSZs([]); setDstDCs([]);
    }
    setLoadingDst(false);
  }, []);

  useEffect(() => {
    loadSrcData(form.environment, form.application);
  }, [form.environment, form.application, loadSrcData]);

  useEffect(() => {
    if (form.dst_application) {
      // Destination has its own app — load its own app-specific NH/SZ/DC
      loadDstData(form.environment, form.dst_application);
    } else if (form.application) {
      // No separate destination app — load source app's data for destination too
      // This ensures destination SZs are app-specific (same app), not "all SZs"
      loadDstData(form.environment, form.application);
    } else {
      setDstNHs([]); setDstSZs([]); setDstDCs([]);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.environment, form.dst_application, form.application, loadDstData]);

  // Helper: collect NH ids from app_dc_mappings for a given app (and optionally component)
  const collectMappingNHs = useCallback((appId: string, component?: string) => {
    const nhSet = new Set<string>();
    for (const m of appDcMappings) {
      const mr = m as Record<string, string>;
      if (mappingMatchesApp(mr, appId) &&
          (!component || mr.component === component) && mr.nh) {
        nhSet.add(mr.nh);
      }
    }
    return nhSet;
  }, [appDcMappings, mappingMatchesApp]);

  const collectMappingSZs = useCallback((appId: string, component?: string) => {
    const szSet = new Set<string>();
    for (const m of appDcMappings) {
      const mr = m as Record<string, string>;
      if (mappingMatchesApp(mr, appId) &&
          (!component || mr.component === component) && mr.sz) {
        szSet.add(mr.sz);
      }
    }
    return szSet;
  }, [appDcMappings, mappingMatchesApp]);

  // Collect DCs from app_dc_mappings for a given app (and optionally component)
  const collectMappingDCs = useCallback((appId: string, component?: string) => {
    const dcSet = new Set<string>();
    for (const m of appDcMappings) {
      const mr = m as Record<string, string>;
      if (mappingMatchesApp(mr, appId) &&
          (!component || mr.component === component)) {
        if (mr.dc) dcSet.add(mr.dc);
        if (mr.legacy_dc) dcSet.add(mr.legacy_dc);
      }
    }
    return dcSet;
  }, [appDcMappings, mappingMatchesApp]);

  // Derive DCs from mappings for source app+component
  const srcMappingDCs = useMemo(() => {
    if (!form.application) return [] as { code: string; name: string; dc_type: string }[];
    const dcSet = collectMappingDCs(form.application, form.src_component || undefined);
    if (dcSet.size > 0) {
      return Array.from(dcSet).map(dc => ({
        code: dc, name: dc,
        dc_type: dc.toUpperCase().includes('NGDC') ? 'NGDC' : 'Legacy'
      }));
    }
    // Fallback to API-loaded DCs
    return srcDCs.map(dc => ({ code: dc.code, name: dc.name, dc_type: 'NGDC' }));
  }, [form.application, form.src_component, collectMappingDCs, srcDCs]);

  // Derive DCs from mappings for destination app+component
  const dstMappingDCs = useMemo(() => {
    const dstApp = form.dst_application || form.application;
    if (!dstApp) return [] as { code: string; name: string; dc_type: string }[];
    const dcSet = collectMappingDCs(dstApp, form.dst_component || undefined);
    if (dcSet.size > 0) {
      return Array.from(dcSet).map(dc => ({
        code: dc, name: dc,
        dc_type: dc.toUpperCase().includes('NGDC') ? 'NGDC' : 'Legacy'
      }));
    }
    return dstDCs.map(dc => ({ code: dc.code, name: dc.name, dc_type: 'NGDC' }));
  }, [form.dst_application, form.application, form.dst_component, collectMappingDCs, dstDCs]);

  // Filter NHs/SZs based on selected component from app_dc_mappings
  // When no component is selected but the app has mappings, use ALL component NHs/SZs
  // instead of falling back to app-level defaults (which may be stale)
  const srcNeighbourhoods = useMemo(() => {
    if (form.application) {
      const nhSet = collectMappingNHs(form.application, form.src_component || undefined);
      if (nhSet.size > 0) {
        const filtered = srcNHs.filter(nh => nhSet.has(nh.nh_id));
        if (filtered.length > 0) return filtered.map(nh => ({ id: nh.nh_id, name: nh.name }));
        // NHs not in srcNHs (API response) — build from fallback list
        return FALLBACK_NEIGHBOURHOODS.filter(nh => nhSet.has(nh.id));
      }
    }
    return srcNHs.length > 0 ? srcNHs.map(nh => ({ id: nh.nh_id, name: nh.name })) : FALLBACK_NEIGHBOURHOODS;
  }, [srcNHs, form.src_component, form.application, collectMappingNHs]);

  const srcZones = useMemo(() => {
    if (form.application) {
      const szSet = collectMappingSZs(form.application, form.src_component || undefined);
      if (szSet.size > 0) {
        const filtered = srcSZs.filter(sz => szSet.has(sz.code));
        if (filtered.length > 0) return filtered.map(sz => ({ code: sz.code, name: sz.name }));
        // SZs not in srcSZs — return raw codes
        return Array.from(szSet).map(code => ({ code, name: code }));
      }
    }
    return srcSZs.length > 0 ? srcSZs.map(sz => ({ code: sz.code, name: sz.name })) : [];
  }, [srcSZs, form.src_component, form.application, collectMappingSZs]);

  const dstNeighbourhoods = useMemo(() => {
    const dstApp = form.dst_application || form.application;
    let result: { id: string; name: string }[];
    if (dstApp) {
      const nhSet = collectMappingNHs(dstApp, form.dst_component || undefined);
      if (nhSet.size > 0) {
        const filtered = dstNHs.filter(nh => nhSet.has(nh.nh_id));
        result = filtered.length > 0 ? filtered.map(nh => ({ id: nh.nh_id, name: nh.name })) : FALLBACK_NEIGHBOURHOODS.filter(nh => nhSet.has(nh.id));
      } else {
        result = dstNHs.length > 0 ? dstNHs.map(nh => ({ id: nh.nh_id, name: nh.name })) : FALLBACK_NEIGHBOURHOODS;
      }
    } else {
      result = dstNHs.length > 0 ? dstNHs.map(nh => ({ id: nh.nh_id, name: nh.name })) : FALLBACK_NEIGHBOURHOODS;
    }
    // Ensure the currently selected destination NH is always present (draft edit restoration)
    if (form.dst_nh && !result.find(nh => nh.id === form.dst_nh)) {
      result = [{ id: form.dst_nh, name: form.dst_nh }, ...result];
    }
    return result;
  }, [dstNHs, form.dst_component, form.dst_application, form.application, form.dst_nh, collectMappingNHs]);

  const dstZones = useMemo(() => {
    const dstApp = form.dst_application || form.application;
    let result: { code: string; name: string }[];
    if (dstApp) {
      const szSet = collectMappingSZs(dstApp, form.dst_component || undefined);
      if (szSet.size > 0) {
        const filtered = dstSZs.filter(sz => szSet.has(sz.code));
        result = filtered.length > 0 ? filtered.map(sz => ({ code: sz.code, name: sz.name })) : Array.from(szSet).map(code => ({ code, name: code }));
      } else {
        result = dstSZs.length > 0 ? dstSZs.map(sz => ({ code: sz.code, name: sz.name })) : [];
      }
    } else {
      result = dstSZs.length > 0 ? dstSZs.map(sz => ({ code: sz.code, name: sz.name })) : [];
    }
    // Ensure the currently selected destination SZ is always present (draft edit restoration)
    if (form.dst_sz && !result.find(sz => sz.code === form.dst_sz)) {
      result = [{ code: form.dst_sz, name: form.dst_sz }, ...result];
    }
    return result;
  }, [dstSZs, form.dst_component, form.dst_application, form.application, form.dst_sz, collectMappingSZs]);

  // Combined datacenter list for backward compat (uses mapping-derived DCs)
  const datacenters = useMemo(() => {
    const all = [...srcMappingDCs, ...dstMappingDCs];
    const seen = new Set<string>();
    const unique: { code: string; name: string }[] = [];
    for (const dc of all) {
      if (!seen.has(dc.code)) { seen.add(dc.code); unique.push({ code: dc.code, name: dc.name }); }
    }
    return unique.length > 0 ? unique : FALLBACK_DATACENTERS;
  }, [srcMappingDCs, dstMappingDCs]);

  // Filter groups by NH, SZ, AND component — match groups whose name contains the codes
  const srcFilteredGroups = useMemo(() => {
    if (!form.src_nh && !form.src_sz && !form.src_component) return srcAppGroups;
    return srcAppGroups.filter(g => {
      const name = g.name.toLowerCase();
      const matchNh = !form.src_nh || name.includes(form.src_nh.toLowerCase());
      const matchSz = !form.src_sz || name.includes(form.src_sz.toLowerCase());
      const matchComp = !form.src_component || name.includes(form.src_component.toLowerCase());
      return matchNh && matchSz && matchComp;
    });
  }, [srcAppGroups, form.src_nh, form.src_sz, form.src_component]);

  const dstFilteredGroups = useMemo(() => {
    if (!form.dst_nh && !form.dst_sz && !form.dst_component) return dstAppGroups;
    return dstAppGroups.filter(g => {
      const name = g.name.toLowerCase();
      const matchNh = !form.dst_nh || name.includes(form.dst_nh.toLowerCase());
      const matchSz = !form.dst_sz || name.includes(form.dst_sz.toLowerCase());
      const matchComp = !form.dst_component || name.includes(form.dst_component.toLowerCase());
      return matchNh && matchSz && matchComp;
    });
  }, [dstAppGroups, form.dst_nh, form.dst_sz, form.dst_component]);

  // Auto-populate NH/SZ when component is selected and there's only one option (Issue 1)
  useEffect(() => {
    if (!form.src_component || !form.application) return;
    const nhSet = collectMappingNHs(form.application, form.src_component);
    const szSet = collectMappingSZs(form.application, form.src_component);
    // Auto-set NH if exactly one match
    if (nhSet.size === 1 && !form.src_nh) {
      const nh = Array.from(nhSet)[0];
      setForm(prev => ({ ...prev, src_nh: nh }));
    }
    // Auto-set SZ if exactly one match
    if (szSet.size === 1 && !form.src_sz) {
      const sz = Array.from(szSet)[0];
      setForm(prev => ({ ...prev, src_sz: sz }));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.src_component, form.application, collectMappingNHs, collectMappingSZs]);

  useEffect(() => {
    const dstApp = form.dst_application || form.application;
    if (!form.dst_component || !dstApp) return;
    const nhSet = collectMappingNHs(dstApp, form.dst_component);
    const szSet = collectMappingSZs(dstApp, form.dst_component);
    if (nhSet.size === 1 && !form.dst_nh) {
      const nh = Array.from(nhSet)[0];
      setForm(prev => ({ ...prev, dst_nh: nh }));
    }
    if (szSet.size === 1 && !form.dst_sz) {
      const sz = Array.from(szSet)[0];
      setForm(prev => ({ ...prev, dst_sz: sz }));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.dst_component, form.dst_application, form.application, collectMappingNHs, collectMappingSZs]);

  // Generate the standard group name for "create new" option
  const srcSuggestedName = useMemo(() => {
    if (!form.application || !form.src_nh || !form.src_sz) return '';
    return `grp-${form.application}-${form.src_nh}-${form.src_sz}-${form.src_subtype}`;
  }, [form.application, form.src_nh, form.src_sz, form.src_subtype]);

  const dstSuggestedName = useMemo(() => {
    const dstApp = form.dst_application || form.application;
    if (!dstApp || !form.dst_nh || !form.dst_sz) return '';
    return `grp-${dstApp}-${form.dst_nh}-${form.dst_sz}-${form.dst_subtype}`;
  }, [form.application, form.dst_application, form.dst_nh, form.dst_sz, form.dst_subtype]);

  // Keep srcName/dstName for backward compat — resolve from form.source/form.destination or suggested
  const srcName = form.src_custom || srcSuggestedName;
  const dstName = form.dst_custom || dstSuggestedName;

  const effectivePort = form.port === 'custom' ? form.customPort : form.port;

  useEffect(() => {
    if (!form.src_sz || !form.dst_sz) { setBirthrightResult(null); return; }
    const timer = setTimeout(async () => {
      setValidatingBR(true);
      try {
        const result = await api.validateBirthright({
          source_zone: form.src_sz, destination_zone: form.dst_sz,
          source_sz: form.src_sz, destination_sz: form.dst_sz,
          source_nh: form.src_nh, destination_nh: form.dst_nh,
          source_dc: form.src_dc || form.datacenter, destination_dc: form.dst_dc || form.datacenter,
          environment: form.environment,
        });
        setBirthrightResult(result);
      } catch { setBirthrightResult(null); }
      setValidatingBR(false);
    }, 400);
    return () => clearTimeout(timer);
  }, [form.src_sz, form.dst_sz, form.src_nh, form.dst_nh, form.datacenter, form.environment, form.src_dc, form.dst_dc]);

  // Birthright already permitted = no FW rule needed, block submission
  const isBirthrightPermitted = birthrightResult
    && birthrightResult.compliant
    && !birthrightResult.firewall_request_required;

  const canStep1 = form.application && form.environment && (form.src_dc || form.datacenter);
  // Source and destination groups are required — rule creation is blocked until both are selected from App Groups
  const srcGroupSelected = !!form.src_custom;
  const dstGroupSelected = !!form.dst_custom;
  const canStep2 = form.src_nh && form.src_sz && form.dst_nh && form.dst_sz && srcGroupSelected && dstGroupSelected;
  const canStep3 = effectivePort && form.protocol;
  const canSubmit = canStep1 && canStep2 && canStep3 && !isBirthrightPermitted;

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setSubmitting(true);
    setDraftCreatedMsg('');
    try {
      const finalSrc = form.src_custom ? autoPrefix(form.src_custom.trim(), 'group') : srcName;
      const finalDst = form.dst_custom ? autoPrefix(form.dst_custom.trim(), 'group') : dstName;
      const effectiveDc = form.src_dc || form.datacenter;
      if (isEditMode && editRule) {
        // Update existing draft rule — persist component info for future edits
        await api.updateRule(editRule.rule_id, {
          application: form.application, environment: form.environment, datacenter: effectiveDc,
          source: { source_type: 'Group', ip_address: null, cidr: null, group_name: finalSrc, ports: effectivePort, neighbourhood: form.src_nh, security_zone: form.src_sz },
          destination: { name: finalDst, security_zone: form.dst_sz, dest_ip: null, ports: effectivePort, is_predefined: false },
          description: form.description,
          source_nh: form.src_nh, destination_nh: form.dst_nh,
          // Persist destination_zone at rule level so draft edit can restore it
          destination_zone: form.dst_sz,
          source_zone: form.src_sz,
          dst_application: form.dst_application || undefined,
          src_component: form.src_component || undefined,
          dst_component: form.dst_component || undefined,
          src_dc: form.src_dc || undefined,
          dst_dc: form.dst_dc || undefined,
        });
        onRuleCreated();
        if (onEditComplete) onEditComplete();
      } else {
        await api.createRule({
          application: form.application, environment: form.environment, datacenter: effectiveDc,
          source: finalSrc, source_zone: form.src_sz,
          destination: finalDst, destination_zone: form.dst_sz,
          port: effectivePort, protocol: form.protocol, action: form.action,
          description: form.description, is_group_to_group: true,
          source_nh: form.src_nh, destination_nh: form.dst_nh,
          dst_application: form.dst_application || undefined,
          src_component: form.src_component || undefined,
          dst_component: form.dst_component || undefined,
          src_dc: form.src_dc || undefined,
          dst_dc: form.dst_dc || undefined,
        });
        onRuleCreated();
        setDraftCreatedMsg(`Rule created successfully! Status: DRAFT. The rule must be submitted for review before it becomes active.`);
        setStep(1);
        setForm(buildDefaultForm());
        setBirthrightResult(null);
      }
    } catch { /* handled by parent */ }
    setSubmitting(false);
  };

  const upd = (field: string, value: string) => setForm(prev => ({ ...prev, [field]: value }));
  const sel = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors';
  const lbl = 'block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1.5';

  const stepClass = (s: number) => {
    if (step === s) return 'border-blue-600 text-blue-700 bg-white';
    if (step > s) return 'border-green-500 text-green-700 bg-green-50/50';
    return 'border-transparent text-gray-500 hover:text-gray-700';
  };
  const dotClass = (s: number) => {
    if (step === s) return 'bg-blue-600 text-white';
    if (step > s) return 'bg-green-500 text-white';
    return 'bg-gray-300 text-white';
  };

  const mainContent = (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
      {/* Step indicators */}
      <div className="flex border-b border-gray-200 bg-gray-50">
        {[{ num: 1, label: 'Application & Environment' }, { num: 2, label: 'Source & Destination' }, { num: 3, label: 'Connection & Review' }].map(s => (
          <button key={s.num} onClick={() => setStep(s.num)}
            className={'flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2 ' + stepClass(s.num)}>
            <span className={'w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ' + dotClass(s.num)}>
              {step > s.num ? '\u2713' : s.num}
            </span>
            <span className="hidden sm:inline">{s.label}</span>
          </button>
        ))}
      </div>

      <div className="p-6">
        {/* Draft created banner */}
        {draftCreatedMsg && (
          <div className="mb-4 p-4 bg-amber-50 border border-amber-300 rounded-lg flex items-start gap-3">
            <span className="text-amber-600 text-lg font-bold">!</span>
            <div>
              <p className="text-sm font-semibold text-amber-800">{draftCreatedMsg}</p>
              <p className="text-xs text-amber-600 mt-1">Go to the Rules list to view, edit, or submit draft rules.</p>
            </div>
            <button onClick={() => setDraftCreatedMsg('')} className="ml-auto text-amber-500 hover:text-amber-700 text-sm font-bold">&times;</button>
          </div>
        )}

        {/* Step 1: Application & Environment */}
        {step === 1 && (
          <div className="space-y-5">
            <div className="grid grid-cols-2 gap-5">
              <div>
                <label className={lbl}>Source Application</label>
                <select className={sel} value={form.application} onChange={e => { upd('application', e.target.value); upd('src_component', ''); upd('src_nh', ''); upd('src_sz', ''); }}>
                  <option value="">Select Source Application...</option>
                  {applications.map(app => (
                    <option key={app.app_distributed_id || app.app_id} value={app.app_distributed_id || app.app_id}>{app.app_distributed_id || app.app_id}</option>
                  ))}
                </select>
                <p className="text-[10px] text-gray-400 mt-1">Populates source component, NH and SZ dropdowns</p>
              </div>
              <div>
                <label className={lbl}>Destination Application</label>
                <select className={sel} value={form.dst_application} onChange={e => { upd('dst_application', e.target.value); upd('dst_component', ''); upd('dst_nh', ''); upd('dst_sz', ''); }}>
                  <option value="">Same as Source / All</option>
                  {applications.map(app => (
                    <option key={app.app_distributed_id || app.app_id} value={app.app_distributed_id || app.app_id}>{app.app_distributed_id || app.app_id}</option>
                  ))}
                </select>
                <p className="text-[10px] text-gray-400 mt-1">Populates destination component, NH and SZ dropdowns</p>
              </div>
            </div>
            {/* Component selection - filters NHs and SZs */}
            <div className="grid grid-cols-2 gap-5">
              <div>
                <label className={lbl}>Source Component</label>
                <select className={sel} value={form.src_component} onChange={e => { upd('src_component', e.target.value); upd('src_nh', ''); upd('src_sz', ''); }}>
                  <option value="">All Components</option>
                  {srcComponents.map(c => (<option key={c} value={c}>{c}</option>))}
                </select>
                <p className="text-[10px] text-gray-400 mt-1">Filters source NHs and SZs per App Management mapping</p>
              </div>
              <div>
                <label className={lbl}>Destination Component</label>
                <select className={sel} value={form.dst_component} onChange={e => { upd('dst_component', e.target.value); upd('dst_nh', ''); upd('dst_sz', ''); }}>
                  <option value="">All Components</option>
                  {dstComponents.map(c => (<option key={c} value={c}>{c}</option>))}
                </select>
                <p className="text-[10px] text-gray-400 mt-1">Filters destination NHs and SZs per App Management mapping</p>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-5">
              <div>
                <label className={lbl}>Environment</label>
                <select className={sel} value={form.environment} onChange={e => { upd('environment', e.target.value); upd('src_nh', ''); upd('src_sz', ''); upd('dst_nh', ''); upd('dst_sz', ''); }}>
                  <option value="Production">Production</option>
                  <option value="Non-Production">Non-Production</option>
                  <option value="Pre-Production">Pre-Production</option>
                </select>
              </div>
              <div>
                <label className={lbl}>Source DC</label>
                <select className={sel} value={form.src_dc} onChange={e => { upd('src_dc', e.target.value); upd('datacenter', e.target.value); }}>
                  <option value="">Select Source DC...</option>
                  {srcMappingDCs.map(dc => (
                    <option key={dc.code} value={dc.code}>{dc.name} ({dc.dc_type})</option>
                  ))}
                  {srcMappingDCs.length === 0 && datacenters.map(dc => (
                    <option key={dc.code} value={dc.code}>{dc.name}</option>
                  ))}
                </select>
                <p className="text-[10px] text-gray-400 mt-1">Filtered by source app + component from Settings</p>
              </div>
              <div>
                <label className={lbl}>Destination DC</label>
                <select className={sel} value={form.dst_dc} onChange={e => upd('dst_dc', e.target.value)}>
                  <option value="">Same as Source</option>
                  {dstMappingDCs.map(dc => (
                    <option key={dc.code} value={dc.code}>{dc.name} ({dc.dc_type})</option>
                  ))}
                  {dstMappingDCs.length === 0 && datacenters.map(dc => (
                    <option key={dc.code} value={dc.code}>{dc.name}</option>
                  ))}
                </select>
                <p className="text-[10px] text-gray-400 mt-1">Filtered by dest app + component from Settings</p>
              </div>
            </div>
            {/* Cross-DC warning */}
            {form.src_dc && form.dst_dc && form.src_dc !== form.dst_dc && (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-center gap-2">
                <span className="text-amber-600 font-bold text-sm">!</span>
                <span className="text-xs text-amber-700 font-medium">Cross-DC rule: Source DC <strong>{form.src_dc}</strong> &rarr; Destination DC <strong>{form.dst_dc}</strong>. Cross-DC birthright validation will be applied.</span>
              </div>
            )}
            {form.application && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <span className="text-sm text-blue-800 font-medium">
                  Building rule: <strong>{form.application}</strong>
                  {form.src_component && <> ({form.src_component})</>}
                  {form.dst_application && form.dst_application !== form.application && (
                    <> &rarr; <strong>{form.dst_application}</strong>{form.dst_component && <> ({form.dst_component})</>}</>
                  )}
                  {' '}in <strong>{form.environment}</strong>
                  {form.src_dc && <> at <strong>{form.src_dc}</strong></>}
                  {form.dst_dc && form.dst_dc !== form.src_dc && <> &rarr; <strong>{form.dst_dc}</strong></>}
                </span>
              </div>
            )}
            <div className="flex justify-end">
              <button onClick={() => setStep(2)} disabled={!canStep1}
                className="px-5 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed">
                Next: Source &amp; Destination &rarr;
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Source & Destination */}
        {step === 2 && (
          <div className="space-y-5">
            <div className="grid grid-cols-[1fr_auto_1fr] gap-4 items-start">
              {/* Source panel */}
              <div className="border border-blue-200 rounded-xl p-4 bg-blue-50/30">
                <div className="flex items-center gap-2 mb-4">
                  <span className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center text-xs font-bold">SRC</span>
                  <h3 className="text-sm font-bold text-blue-800">Source</h3>
                  {form.application && <span className="text-[10px] text-blue-500 bg-blue-100 px-1.5 py-0.5 rounded">App: {form.application}</span>}
                </div>
                <div className="space-y-3">
                  <div>
                    <label className={lbl}>Neighbourhood</label>
                    <select className={sel} value={form.src_nh} onChange={e => upd('src_nh', e.target.value)}>
                      <option value="">Select Neighbourhood...</option>
                      {srcNeighbourhoods.map(nh => (<option key={nh.id} value={nh.id}>{nh.id} - {nh.name}</option>))}
                    </select>
                    {loadingSrc && <span className="text-[10px] text-blue-500 animate-pulse">Loading...</span>}
                  </div>
                  <div>
                    <label className={lbl}>Security Zone</label>
                    <select className={sel} value={form.src_sz} onChange={e => upd('src_sz', e.target.value)}>
                      <option value="">Select Zone...</option>
                      {srcZones.map(z => (<option key={z.code} value={z.code}>{z.code} - {z.name}</option>))}
                    </select>
                  </div>
                  <div>
                    <label className={lbl}>Source Group</label>
                    {srcFilteredGroups.length > 0 ? (
                      <>
                        <select className={sel} value={form.src_custom} onChange={e => upd('src_custom', e.target.value)}>
                          <option value="">Select Existing Group...</option>
                          {srcFilteredGroups.map(g => (
                            <option key={g.name} value={g.name}>{g.name} ({g.members.length} members)</option>
                          ))}
                        </select>
                        <p className="text-[10px] text-gray-400 mt-0.5">{srcFilteredGroups.length} group(s) match {form.src_nh && `NH: ${form.src_nh}`}{form.src_nh && form.src_sz && ', '}{form.src_sz && `SZ: ${form.src_sz}`}</p>
                      </>
                    ) : form.application && form.src_nh && form.src_sz ? (
                      <div className="p-3 bg-red-50 border border-red-300 rounded-lg">
                        <p className="text-xs text-red-700 font-bold mb-1">No source group exists for {form.application} in {form.src_nh}/{form.src_sz}</p>
                        <p className="text-[10px] text-red-600 mb-2">A source group is required. Select component to generate name, then create the group:</p>
                        <select className={sel + ' mb-2'} value={form.src_subtype} onChange={e => { upd('src_subtype', e.target.value); upd('src_custom', ''); }}>
                          {(srcComponents.length > 0 ? srcComponents : SUBTYPES.map(s => s.code)).map(c => (<option key={c} value={c}>{c}</option>))}
                        </select>
                        {srcSuggestedName && (
                          <div className="space-y-1.5">
                            <div className="px-2 py-1.5 text-xs bg-white border border-red-200 rounded font-mono text-red-700">{srcSuggestedName}</div>
                            <button onClick={() => { setNewGroupName(srcSuggestedName); setNewGroupMembers([]); setCreateGroupForDst(false); setGroupPolicyResult(null); setGroupCompiledPolicy(null); setShowCreateGroupModal(true); }}
                              className="w-full px-3 py-2 text-xs font-bold text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors">
                              Create Group: {srcSuggestedName}
                            </button>
                          </div>
                        )}
                        <p className="text-[10px] text-red-500 mt-2 font-semibold">Rule creation is blocked until a source group is created or selected.</p>
                      </div>
                    ) : (
                      <select className={sel} disabled>
                        <option value="">Select NH &amp; SZ first...</option>
                      </select>
                    )}
                    {form.src_custom && (
                      <div className="mt-1 p-2 bg-white border border-blue-200 rounded-lg">
                        <div className="text-[10px] font-semibold text-gray-500 uppercase mb-0.5">Selected Group</div>
                        <code className="text-xs font-mono text-blue-700 break-all">{form.src_custom}</code>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Arrow connector */}
              <div className="flex flex-col items-center justify-center pt-12 gap-2">
                <div className="w-px h-8 bg-gray-300" />
                <div className="w-10 h-10 rounded-full bg-amber-100 border-2 border-amber-400 flex items-center justify-center">
                  <span className="text-amber-700 text-lg font-bold">&rarr;</span>
                </div>
                <div className="text-[10px] text-gray-400 font-semibold uppercase">Policy</div>
                {validatingBR && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-amber-600" />}
                {birthrightResult && !validatingBR && (
                  <span className={'px-2 py-0.5 rounded-full text-[10px] font-bold ' + (
                    isBirthrightPermitted ? 'bg-green-100 text-green-700' :
                    birthrightResult.firewall_request_required ? 'bg-amber-100 text-amber-700' :
                    birthrightResult.compliant ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  )}>
                    {isBirthrightPermitted ? 'ALREADY PERMITTED' :
                     birthrightResult.firewall_request_required ? 'FW REQUIRED' :
                     birthrightResult.compliant ? 'PERMITTED' : 'BLOCKED'}
                  </span>
                )}
                <div className="w-px h-8 bg-gray-300" />
              </div>

              {/* Destination panel */}
              <div className="border border-emerald-200 rounded-xl p-4 bg-emerald-50/30">
                <div className="flex items-center gap-2 mb-4">
                  <span className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center text-xs font-bold">DST</span>
                  <h3 className="text-sm font-bold text-emerald-800">Destination</h3>
                  {(form.dst_application || form.application) && <span className="text-[10px] text-emerald-500 bg-emerald-100 px-1.5 py-0.5 rounded">App: {form.dst_application || form.application}</span>}
                </div>
                <div className="space-y-3">
                  <div>
                    <label className={lbl}>Neighbourhood</label>
                    <select className={sel} value={form.dst_nh} onChange={e => upd('dst_nh', e.target.value)}>
                      <option value="">Select Neighbourhood...</option>
                      {dstNeighbourhoods.map(nh => (<option key={nh.id} value={nh.id}>{nh.id} - {nh.name}</option>))}
                    </select>
                    {loadingDst && <span className="text-[10px] text-emerald-500 animate-pulse">Loading...</span>}
                  </div>
                  <div>
                    <label className={lbl}>Security Zone</label>
                    <select className={sel} value={form.dst_sz} onChange={e => upd('dst_sz', e.target.value)}>
                      <option value="">Select Zone...</option>
                      {dstZones.map(z => (<option key={z.code} value={z.code}>{z.code} - {z.name}</option>))}
                    </select>
                  </div>
                  <div>
                    <label className={lbl}>Destination Group</label>
                    {dstFilteredGroups.length > 0 ? (
                      <>
                        <select className={sel} value={form.dst_custom} onChange={e => upd('dst_custom', e.target.value)}>
                          <option value="">Select Existing Group...</option>
                          {dstFilteredGroups.map(g => (
                            <option key={g.name} value={g.name}>{g.name} ({g.members.length} members)</option>
                          ))}
                        </select>
                        <p className="text-[10px] text-gray-400 mt-0.5">{dstFilteredGroups.length} group(s) match {form.dst_nh && `NH: ${form.dst_nh}`}{form.dst_nh && form.dst_sz && ', '}{form.dst_sz && `SZ: ${form.dst_sz}`}</p>
                      </>
                    ) : (form.dst_application || form.application) && form.dst_nh && form.dst_sz ? (
                      <div className="p-3 bg-red-50 border border-red-300 rounded-lg">
                        <p className="text-xs text-red-700 font-bold mb-1">No destination group exists for {form.dst_application || form.application} in {form.dst_nh}/{form.dst_sz}</p>
                        <p className="text-[10px] text-red-600 mb-2">Please re-check your destination Application, Component, NH, and SZ selections. The destination group must already exist in App Groups before creating a firewall rule.</p>
                        <p className="text-[10px] text-red-500 font-semibold">Rule creation is blocked until a valid destination group is selected.</p>
                      </div>
                    ) : (
                      <select className={sel} disabled>
                        <option value="">Select NH &amp; SZ first...</option>
                      </select>
                    )}
                    {form.dst_custom && (
                      <div className="mt-1 p-2 bg-white border border-emerald-200 rounded-lg">
                        <div className="text-[10px] font-semibold text-gray-500 uppercase mb-0.5">Selected Group</div>
                        <code className="text-xs font-mono text-emerald-700 break-all">{form.dst_custom}</code>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {birthrightResult && !validatingBR && (
              <div className="space-y-2">
                {/* Already permitted - block submission */}
                {isBirthrightPermitted && (
                  <div className="p-4 rounded-lg border-2 border-green-400 bg-green-50">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-bold text-green-800">Already Permitted &mdash; No Firewall Rule Needed</span>
                    </div>
                    <p className="text-sm text-green-700">
                      This traffic is already allowed by birthright policy. No additional firewall rule is required.
                      You cannot submit a rule for traffic that is already permitted.
                    </p>
                    {birthrightResult.permitted.length > 0 && (
                      <ul className="text-xs text-green-700 list-disc list-inside mt-2">
                        {birthrightResult.permitted.map((p, i) => (<li key={i}>{p.rule} &mdash; {p.reason}</li>))}
                      </ul>
                    )}
                  </div>
                )}
                {/* Policy Status */}
                {!isBirthrightPermitted && <div className={'p-3 rounded-lg border text-sm ' + (
                  birthrightResult.firewall_request_required ? 'bg-amber-50 border-amber-200' :
                  birthrightResult.compliant ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                )}>
                  <div className="flex items-center gap-2 mb-1">
                    <span className={'font-bold text-xs ' + (
                      birthrightResult.firewall_request_required ? 'text-amber-700' :
                      birthrightResult.compliant ? 'text-green-700' : 'text-red-700'
                    )}>
                      Policy: {birthrightResult.matrix_used || ''}
                    </span>
                    <span className={'text-xs ' + (
                      birthrightResult.firewall_request_required ? 'text-amber-600' :
                      birthrightResult.compliant ? 'text-green-600' : 'text-red-600'
                    )}>
                      {birthrightResult.firewall_request_required
                        ? 'Firewall rule required for this cross-zone traffic'
                        : birthrightResult.compliant ? 'Permitted' : 'Blocked by policy'}
                    </span>
                  </div>
                  {birthrightResult.permitted.length > 0 && (
                    <ul className="text-xs text-green-700 list-disc list-inside mt-1">
                      {birthrightResult.permitted.map((p, i) => (<li key={i}>{p.rule} &mdash; {p.reason}</li>))}
                    </ul>
                  )}
                  {birthrightResult.warnings.length > 0 && (
                    <ul className="text-xs text-amber-700 list-disc list-inside mt-1">
                      {birthrightResult.warnings.map((w, i) => (<li key={i}>{w.rule} &mdash; {w.reason}</li>))}
                    </ul>
                  )}
                </div>}

                {/* Firewall Device Hops — rule required */}
                {birthrightResult.firewall_devices_needed && birthrightResult.firewall_devices_needed.length > 0 && (
                  <div className="p-3 rounded-lg border border-amber-300 bg-amber-50 text-sm">
                    <div className="font-bold text-xs text-amber-800 mb-1">Firewall Rule Required — {birthrightResult.firewall_devices_needed.length} device{birthrightResult.firewall_devices_needed.length > 1 ? 's' : ''}</div>
                    <div className="flex flex-wrap gap-2">
                      {birthrightResult.firewall_devices_needed.map((dev, i) => (
                        <span key={i} className="inline-flex items-center gap-1 px-2 py-1 rounded bg-white border border-amber-300 text-xs font-mono text-amber-800">
                          {dev}
                        </span>
                      ))}
                    </div>
                    <div className="text-[10px] text-amber-600 mt-1">
                      DC: {datacenters.find(d => d.code === form.datacenter)?.name || form.datacenter}
                    </div>
                  </div>
                )}

                {/* Informational FW path — same SZ cross NH (permitted, no rule required) */}
                {birthrightResult.firewall_path_info && birthrightResult.firewall_path_info.length > 0 && !birthrightResult.firewall_request_required && (
                  <div className="p-3 rounded-lg border border-blue-200 bg-blue-50/50 text-sm">
                    <div className="font-bold text-xs text-blue-700 mb-1">Traffic Path (informational — no firewall rule required)</div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="px-2 py-1 rounded bg-blue-100 border border-blue-200 text-xs font-mono text-blue-800">{form.src_nh} {form.src_sz}</span>
                      {birthrightResult.firewall_path_info.map((fw, i) => (
                        <span key={i} className="inline-flex items-center gap-1">
                          <span className="text-gray-400">&rarr;</span>
                          <span className="px-2 py-1 rounded bg-white border border-blue-200 text-xs font-mono text-blue-700">{fw}</span>
                        </span>
                      ))}
                      <span className="text-gray-400">&rarr;</span>
                      <span className="px-2 py-1 rounded bg-purple-100 border border-purple-200 text-xs font-mono text-purple-800">{form.dst_nh} {form.dst_sz}</span>
                    </div>
                    <div className="text-[10px] text-blue-500 mt-1">
                      DC: {datacenters.find(d => d.code === form.datacenter)?.name || form.datacenter} — Permitted per birthright
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Source group required message */}
            {form.src_nh && form.src_sz && !srcGroupSelected && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-xs font-semibold text-red-700">Source group is required to proceed. Please select or create a source group from App Groups above.</p>
              </div>
            )}

            <div className="flex justify-between">
              <button onClick={() => setStep(1)} className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50">
                &larr; Back
              </button>
              <button onClick={() => setStep(3)} disabled={!canStep2}
                className="px-5 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed">
                Next: Connection Details &rarr;
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Connection & Review */}
        {step === 3 && (
          <div className="space-y-5">
            <div className="grid grid-cols-3 gap-5">
              <div>
                <label className={lbl}>Port</label>
                <select className={sel} value={form.port} onChange={e => upd('port', e.target.value)}>
                  {COMMON_PORTS.map(p => (<option key={p.value} value={p.value}>{p.label}</option>))}
                  <option value="custom">Custom Port...</option>
                </select>
                {form.port === 'custom' && (
                  <input className={sel + ' mt-2'} placeholder="e.g. 8443, 9090-9095" value={form.customPort} onChange={e => upd('customPort', e.target.value)} />
                )}
              </div>
              <div>
                <label className={lbl}>Protocol</label>
                <select className={sel} value={form.protocol} onChange={e => upd('protocol', e.target.value)}>
                  {PROTOCOLS.map(p => (<option key={p} value={p}>{p}</option>))}
                </select>
              </div>
              <div>
                <label className={lbl}>Action</label>
                <select className={sel} value={form.action} onChange={e => upd('action', e.target.value)}>
                  <option value="Allow">Allow</option>
                  <option value="Deny">Deny</option>
                </select>
              </div>
            </div>

            <div>
              <label className={lbl}>Description (optional)</label>
              <textarea className={sel + ' h-16 resize-none'} placeholder="Brief description of this rule..." value={form.description} onChange={e => upd('description', e.target.value)} />
            </div>

            {/* Birthright block banner */}
            {isBirthrightPermitted && (
              <div className="p-4 rounded-lg border-2 border-green-400 bg-green-50">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-green-800">Already Permitted &mdash; No Firewall Rule Needed</span>
                </div>
                <p className="text-sm text-green-700 mt-1">
                  This traffic is already allowed by birthright policy. Rule creation is blocked.
                </p>
              </div>
            )}

            {/* Review summary */}
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
              <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Rule Summary</h4>
              <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Source App:</span>
                  <span className="font-medium text-gray-900">{form.application || '\u2014'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Destination App:</span>
                  <span className="font-medium text-gray-900">{form.dst_application || form.application || '\u2014'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Environment:</span>
                  <span className="font-medium text-gray-900">{form.environment}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Datacenter:</span>
                  <span className="font-medium text-gray-900">{datacenters.find(d => d.code === form.datacenter)?.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Protocol/Port:</span>
                  <span className="font-medium text-gray-900">{form.protocol}/{effectivePort}</span>
                </div>
                <div className="col-span-2 border-t border-gray-200 pt-2 mt-1">
                  <div className="flex items-center gap-3">
                    <div className="flex-1">
                      <div className="text-[10px] text-gray-500 font-semibold uppercase">Source</div>
                      <code className="text-xs font-mono text-blue-700">{form.src_custom || srcName || '\u2014'}</code>
                      <div className="text-[10px] text-gray-400">{form.src_nh} / {form.src_sz}</div>
                    </div>
                    <span className="text-gray-400 text-lg font-bold">&rarr;</span>
                    <div className="flex-1 text-right">
                      <div className="text-[10px] text-gray-500 font-semibold uppercase">Destination</div>
                      <code className="text-xs font-mono text-emerald-700">{form.dst_custom || dstName || '\u2014'}</code>
                      <div className="text-[10px] text-gray-400">{form.dst_nh} / {form.dst_sz}</div>
                    </div>
                  </div>
                </div>
                {birthrightResult && (
                  <div className="col-span-2 mt-1 space-y-1">
                    <span className={'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold ' + (
                      isBirthrightPermitted ? 'bg-green-100 text-green-700' :
                      birthrightResult.firewall_request_required ? 'bg-amber-100 text-amber-700' :
                      birthrightResult.compliant ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    )}>
                      {isBirthrightPermitted
                        ? 'Already Permitted \u2014 No FW Rule Needed'
                        : birthrightResult.firewall_request_required
                        ? 'Firewall Rule Required'
                        : birthrightResult.compliant ? 'Policy: Permitted' : 'Policy: Blocked'}
                    </span>
                    {birthrightResult.firewall_devices_needed && birthrightResult.firewall_devices_needed.length > 0 && (
                      <div className="text-[10px] text-blue-700 font-mono">
                        {birthrightResult.firewall_devices_needed.join(' → ')}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-between">
              <button onClick={() => setStep(2)} className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50">
                &larr; Back
              </button>
              <button onClick={handleSubmit} disabled={!canSubmit || submitting}
                className="px-6 py-2.5 text-sm font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm">
                {submitting ? (isEditMode ? 'Updating...' : 'Creating...') : isBirthrightPermitted ? 'Already Permitted (Cannot Create)' : isEditMode ? 'Update Firewall Rule' : 'Create Firewall Rule'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  /* eslint-disable @typescript-eslint/no-unused-vars */
  /* ---------- Group auto-creation modal (Issue 5) + Policy Change Review ---------- */
  const [groupPolicySubmitted, setGroupPolicySubmitted] = useState(false);
  const [groupPolicyResult, setGroupPolicyResult] = useState<string | null>(null);
  const [groupCompileVendor, setGroupCompileVendor] = useState('palo_alto');
  const [groupCompiledPolicy, setGroupCompiledPolicy] = useState<string | null>(null);

  // Generate device-specific compile output for a newly created group
  const generateGroupCompile = (groupName: string, members: string[], vendor: string): string => {
    const ts = new Date().toISOString();
    switch (vendor) {
      case 'palo_alto': {
        let p = `# Palo Alto PAN-OS Address Group Configuration\n# Group: ${groupName}\n# Generated: ${ts}\n\n`;
        for (const m of members) {
          const objName = m.replace(/[./]/g, '_');
          p += m.includes('/') ? `set address ${objName} ip-netmask ${m}\n` : `set address ${objName} ip-netmask ${m}/32\n`;
        }
        p += `\nset address-group ${groupName} static [ ${members.map(m => m.replace(/[./]/g, '_')).join(' ')} ]\nset address-group ${groupName} description "Auto-created for ${form.application}"\n`;
        return p;
      }
      case 'checkpoint': {
        let p = `# Check Point SmartConsole CLI\n# Group: ${groupName}\n# Generated: ${ts}\n\n`;
        for (const m of members) {
          const objName = m.replace(/[./]/g, '_');
          p += m.includes('/') ? `add network name ${objName} subnet ${m.split('/')[0]} mask-length ${m.split('/')[1]}\n` : `add host name ${objName} ip-address ${m}\n`;
        }
        p += `\nadd group name ${groupName}\n`;
        for (const m of members) p += `set group name ${groupName} members.add ${m.replace(/[./]/g, '_')}\n`;
        return p;
      }
      case 'fortigate': {
        let p = `# FortiGate CLI\n# Group: ${groupName}\n# Generated: ${ts}\n\nconfig firewall address\n`;
        for (const m of members) {
          const objName = m.replace(/[./]/g, '_');
          p += `  edit "${objName}"\n    set type ${m.includes('/') ? 'ipmask' : 'ipmask'}\n    set subnet ${m.includes('/') ? m : m + '/32'}\n  next\n`;
        }
        p += `end\n\nconfig firewall addrgrp\n  edit "${groupName}"\n    set member ${members.map(m => `"${m.replace(/[./]/g, '_')}"`).join(' ')}\n    set comment "Auto-created for ${form.application}"\n  next\nend\n`;
        return p;
      }
      default: {
        let p = `# Generic Group Policy\n# Group: ${groupName}\n# Generated: ${ts}\n\nGROUP_NAME=${groupName}\nGROUP_TYPE=address-group\n\n`;
        for (const m of members) p += `MEMBER type=${m.includes('/') ? 'subnet' : 'ip'} value=${m}\n`;
        return p;
      }
    }
  };

  /** Helper: add a member row in the create-group wizard */
  const handleWizAddMember = () => {
    if (!wizMemberValue.trim()) return;
    const prefixed = autoPrefix(wizMemberValue.trim(), wizMemberType as 'ip' | 'subnet' | 'cidr' | 'group' | 'range');
    setNewGroupMembers(prev => [...prev, { type: wizMemberType, value: prefixed }]);
    setWizMemberValue('');
  };

  /** Member-type display helpers */
  const memberTypeLabel = (t: string) => t === 'cidr' || t === 'subnet' ? 'NET' : t === 'range' ? 'RNG' : t === 'group' ? 'GRP' : 'IP';
  const memberTypeColor = (t: string) => t === 'cidr' || t === 'subnet' ? 'bg-purple-100 text-purple-700' : t === 'range' ? 'bg-orange-100 text-orange-700' : t === 'group' ? 'bg-emerald-100 text-emerald-700' : 'bg-blue-100 text-blue-700';

  const groupModal = showCreateGroupModal && (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6 space-y-4 max-h-[90vh] overflow-y-auto">
        <h3 className="text-lg font-bold text-gray-800">Create Group in App Groups</h3>
        <p className="text-sm text-gray-600">The group <code className="font-mono text-blue-700 bg-blue-50 px-1 rounded">{newGroupName}</code> does not exist. Create it now to continue.</p>
        {/* Policy Change Notice */}
        <div className="p-2.5 bg-amber-50 border border-amber-200 rounded-lg">
          <p className="text-xs font-semibold text-amber-800">Policy Change Review Required</p>
          <p className="text-[10px] text-amber-600 mt-0.5">Creating this group will automatically submit a policy change for review &amp; approval. The compiled device policy will be generated for the selected vendor.</p>
        </div>
        {/* Editable group name */}
        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Group Name</label>
          <input className="w-full px-3 py-2 border rounded-lg text-sm font-mono" value={newGroupName} onChange={e => setNewGroupName(e.target.value)} placeholder="grp-APP01-NH01-STD-WEB" />
        </div>
        {/* Members list with add/remove */}
        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Group Members (IPs / Subnets / Ranges)</label>
          {newGroupMembers.length === 0 && <p className="text-xs text-amber-600 italic mb-2">Add at least one IP, subnet, or range to this group.</p>}
          {newGroupMembers.map((m, mi) => (
            <div key={mi} className="flex items-center gap-2 mb-1 px-2 py-1 bg-gray-50 rounded border border-gray-200">
              <span className={`px-1.5 py-0.5 text-[9px] font-bold rounded ${memberTypeColor(m.type)}`}>{memberTypeLabel(m.type)}</span>
              <span className="font-mono text-xs flex-1">{m.value}</span>
              <button onClick={() => setNewGroupMembers(prev => prev.filter((_, i) => i !== mi))} className="text-red-500 text-[10px] hover:text-red-700">Remove</button>
            </div>
          ))}
          <div className="flex gap-1.5 items-center mt-2">
            <select value={wizMemberType} onChange={e => setWizMemberType(e.target.value)} className="px-1.5 py-1 text-xs border border-gray-300 rounded">
              <option value="ip">IP (svr-)</option>
              <option value="subnet">Subnet (net-)</option>
              <option value="range">Range (rng-)</option>
              <option value="group">Group (grp-)</option>
            </select>
            <input type="text" value={wizMemberValue} onChange={e => setWizMemberValue(e.target.value)}
              placeholder={wizMemberType === 'ip' ? '10.0.1.5' : wizMemberType === 'subnet' ? '10.0.1.0/24' : wizMemberType === 'range' ? '10.0.1.1-10.0.1.50' : 'grp-name'}
              className="flex-1 px-2 py-1 text-xs font-mono border border-gray-300 rounded"
              onKeyDown={e => { if (e.key === 'Enter') handleWizAddMember(); }} />
            <button onClick={handleWizAddMember} disabled={!wizMemberValue.trim()} className="px-2 py-1 text-xs font-medium text-white bg-blue-600 rounded hover:bg-blue-700 disabled:bg-gray-300">Add</button>
          </div>
        </div>
        {/* Compile device type selector */}
        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Compile Preview (Device Type)</label>
          <select className="w-full px-3 py-2 border rounded-lg text-sm" value={groupCompileVendor} onChange={e => { setGroupCompileVendor(e.target.value); setGroupCompiledPolicy(null); }}>
            <option value="palo_alto">Palo Alto PAN-OS</option>
            <option value="checkpoint">Check Point SmartConsole</option>
            <option value="fortigate">FortiGate CLI</option>
            <option value="generic">Generic</option>
          </select>
        </div>
        {/* Preview compile output */}
        {newGroupMembers.length > 0 && (
          <div>
            <button onClick={() => {
              const vals = newGroupMembers.map(m => m.value);
              setGroupCompiledPolicy(generateGroupCompile(newGroupName, vals, groupCompileVendor));
            }} className="px-3 py-1.5 text-xs font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-lg hover:bg-indigo-100 mb-2">
              Preview Compiled Policy
            </button>
            {groupCompiledPolicy && (
              <pre className="bg-gray-900 text-green-400 text-[10px] font-mono p-3 rounded-lg overflow-x-auto max-h-[150px] overflow-y-auto whitespace-pre leading-relaxed">
                {groupCompiledPolicy}
              </pre>
            )}
          </div>
        )}
        {/* Policy submission result */}
        {groupPolicyResult && (
          <div className={`p-2 rounded text-xs font-medium ${groupPolicyResult.includes('Failed') ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
            {groupPolicyResult}
          </div>
        )}
        <div className="flex justify-end gap-3">
          <button onClick={() => { setShowCreateGroupModal(false); setGroupCompiledPolicy(null); setGroupPolicyResult(null); setGroupPolicySubmitted(false); setCreateGroupForDst(false); }} className="px-4 py-2 text-sm text-gray-600 border rounded-lg hover:bg-gray-50">Cancel</button>
          <button disabled={creatingGroup || !newGroupName.trim() || newGroupMembers.length === 0} onClick={async () => {
            setCreatingGroup(true);
            try {
              const nh = createGroupForDst ? form.dst_nh : form.src_nh;
              const sz = createGroupForDst ? form.dst_sz : form.src_sz;
              const comp = createGroupForDst ? (form.dst_component || form.dst_subtype || '') : (form.src_component || form.src_subtype || '');
              // Create the group via API
              await api.createGroup({
                name: newGroupName,
                app_id: form.application,
                nh,
                sz,
                subtype: comp,
                description: `Created for ${form.application} in ${nh}/${sz}`,
                members: newGroupMembers.map(m => ({ type: m.type, value: m.value, description: '' })),
              });
              // Submit policy change for review & approval
              const memberVals = newGroupMembers.map(m => m.value);
              try {
                const policyResult = await api.submitGroupPolicyChanges(
                  newGroupName,
                  'group_created',
                  `Group ${newGroupName} created with ${newGroupMembers.length} member(s) for ${form.application}. Compiled for ${groupCompileVendor}.`,
                  { added: { [`group:${newGroupName}`]: memberVals }, removed: {}, changed: {},
                    compile_vendor: groupCompileVendor,
                    compiled_policy: generateGroupCompile(newGroupName, memberVals, groupCompileVendor) }
                );
                setGroupPolicySubmitted(true);
                setGroupPolicyResult(`Policy change submitted — ${policyResult.affected_rules} affected rule(s) sent for review`);
              } catch {
                setGroupPolicyResult('Group created but policy change submission failed — submit manually from Review page');
              }
              // Select the newly created group in the appropriate field
              if (createGroupForDst) {
                upd('dst_custom', newGroupName);
              } else {
                upd('src_custom', newGroupName);
              }
              onRuleCreated(); // trigger refresh so the new group appears in dropdowns
            } catch {
              setGroupPolicyResult('Failed to create group — check for duplicates');
            }
            setCreatingGroup(false);
          }} className="px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50">
            {creatingGroup ? 'Creating & Submitting...' : `Create Group with ${newGroupMembers.length} member${newGroupMembers.length !== 1 ? 's' : ''}`}
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {groupModal}
      {mainContent}
    </>
  );
}
