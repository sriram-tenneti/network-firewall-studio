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
    application: '', dst_application: '', environment: 'Production', datacenter: 'ALPHA_NGDC',
    src_component: '', dst_component: '',
    src_nh: '', src_sz: '', src_subtype: 'APP', src_custom: '',
    dst_nh: '', dst_sz: '', dst_subtype: 'APP', dst_custom: '',
    port: '443', customPort: '', protocol: 'TCP', action: 'Allow', description: '',
  });

  const [form, setForm] = useState(buildDefaultForm);

  // Pre-populate form when editing a draft rule
  useEffect(() => {
    if (!editRule) return;
    const src = editRule.source;
    const dst = editRule.destination;
    const srcGroup = (src?.group_name || src?.ip_address || src?.cidr || '') as string;
    const dstGroup = (dst?.name || dst?.dest_ip || '') as string;
    const srcSz = (src?.security_zone || '') as string;
    const dstSz = (dst?.security_zone || '') as string;
    const srcNh = (src?.neighbourhood || '') as string;
    const ports = (src?.ports || dst?.ports || '') as string;
    // Try to find dst_application from the rule (stored as extra field)
    const ruleAny = editRule as unknown as Record<string, string>;
    const dstApp = ruleAny.dst_application || '';
    const dstNh = ruleAny.destination_nh || '';
    setForm({
      application: editRule.application || '',
      dst_application: dstApp,
      environment: editRule.environment || 'Production',
      datacenter: editRule.datacenter || 'ALPHA_NGDC',
      src_component: '', dst_component: '',
      src_nh: srcNh, src_sz: srcSz, src_subtype: 'APP', src_custom: srcGroup,
      dst_nh: dstNh, dst_sz: dstSz, dst_subtype: 'APP', dst_custom: dstGroup,
      port: ports || '443', customPort: '', protocol: 'TCP', action: 'Allow', description: '',
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

  // Derive available components for source app from app_dc_mappings
  const srcComponents = useMemo(() => {
    if (!form.application) return [] as string[];
    const comps = new Set<string>();
    for (const m of appDcMappings) {
      const mid = (m as Record<string, string>).app_distributed_id || (m as Record<string, string>).app_id;
      if (mid === form.application && (m as Record<string, string>).component) {
        comps.add((m as Record<string, string>).component);
      }
    }
    return Array.from(comps).sort();
  }, [form.application, appDcMappings]);

  // Derive available components for destination app
  const dstComponents = useMemo(() => {
    const dstApp = form.dst_application || form.application;
    if (!dstApp) return [] as string[];
    const comps = new Set<string>();
    for (const m of appDcMappings) {
      const mid = (m as Record<string, string>).app_distributed_id || (m as Record<string, string>).app_id;
      if (mid === dstApp && (m as Record<string, string>).component) {
        comps.add((m as Record<string, string>).component);
      }
    }
    return Array.from(comps).sort();
  }, [form.dst_application, form.application, appDcMappings]);

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
      const mid = mr.app_distributed_id || mr.app_id;
      if ((mid === appId || mr.app_id === appId || mr.app_distributed_id === appId) &&
          (!component || mr.component === component) && mr.nh) {
        nhSet.add(mr.nh);
      }
    }
    return nhSet;
  }, [appDcMappings]);

  const collectMappingSZs = useCallback((appId: string, component?: string) => {
    const szSet = new Set<string>();
    for (const m of appDcMappings) {
      const mr = m as Record<string, string>;
      const mid = mr.app_distributed_id || mr.app_id;
      if ((mid === appId || mr.app_id === appId || mr.app_distributed_id === appId) &&
          (!component || mr.component === component) && mr.sz) {
        szSet.add(mr.sz);
      }
    }
    return szSet;
  }, [appDcMappings]);

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
    if (dstApp) {
      const nhSet = collectMappingNHs(dstApp, form.dst_component || undefined);
      if (nhSet.size > 0) {
        const filtered = dstNHs.filter(nh => nhSet.has(nh.nh_id));
        if (filtered.length > 0) return filtered.map(nh => ({ id: nh.nh_id, name: nh.name }));
        return FALLBACK_NEIGHBOURHOODS.filter(nh => nhSet.has(nh.id));
      }
    }
    return dstNHs.length > 0 ? dstNHs.map(nh => ({ id: nh.nh_id, name: nh.name })) : FALLBACK_NEIGHBOURHOODS;
  }, [dstNHs, form.dst_component, form.dst_application, form.application, collectMappingNHs]);

  const dstZones = useMemo(() => {
    const dstApp = form.dst_application || form.application;
    if (dstApp) {
      const szSet = collectMappingSZs(dstApp, form.dst_component || undefined);
      if (szSet.size > 0) {
        const filtered = dstSZs.filter(sz => szSet.has(sz.code));
        if (filtered.length > 0) return filtered.map(sz => ({ code: sz.code, name: sz.name }));
        return Array.from(szSet).map(code => ({ code, name: code }));
      }
    }
    return dstSZs.length > 0 ? dstSZs.map(sz => ({ code: sz.code, name: sz.name })) : [];
  }, [dstSZs, form.dst_component, form.dst_application, form.application, collectMappingSZs]);

  const datacenters = useMemo(() => {
    const all = [...srcDCs, ...dstDCs];
    const seen = new Set<string>();
    const unique: { code: string; name: string }[] = [];
    for (const dc of all) {
      const key = dc.code;
      if (!seen.has(key)) { seen.add(key); unique.push({ code: key, name: dc.name }); }
    }
    return unique.length > 0 ? unique : FALLBACK_DATACENTERS;
  }, [srcDCs, dstDCs]);

  // Filter groups by NH and SZ — match groups whose name contains the NH and SZ codes
  const srcFilteredGroups = useMemo(() => {
    if (!form.src_nh && !form.src_sz) return srcAppGroups;
    return srcAppGroups.filter(g => {
      const name = g.name.toLowerCase();
      const matchNh = !form.src_nh || name.includes(form.src_nh.toLowerCase());
      const matchSz = !form.src_sz || name.includes(form.src_sz.toLowerCase());
      return matchNh && matchSz;
    });
  }, [srcAppGroups, form.src_nh, form.src_sz]);

  const dstFilteredGroups = useMemo(() => {
    if (!form.dst_nh && !form.dst_sz) return dstAppGroups;
    return dstAppGroups.filter(g => {
      const name = g.name.toLowerCase();
      const matchNh = !form.dst_nh || name.includes(form.dst_nh.toLowerCase());
      const matchSz = !form.dst_sz || name.includes(form.dst_sz.toLowerCase());
      return matchNh && matchSz;
    });
  }, [dstAppGroups, form.dst_nh, form.dst_sz]);

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
          source_dc: form.datacenter, destination_dc: form.datacenter,
          environment: form.environment,
        });
        setBirthrightResult(result);
      } catch { setBirthrightResult(null); }
      setValidatingBR(false);
    }, 400);
    return () => clearTimeout(timer);
  }, [form.src_sz, form.dst_sz, form.src_nh, form.dst_nh, form.datacenter, form.environment]);

  // Birthright already permitted = no FW rule needed, block submission
  const isBirthrightPermitted = birthrightResult
    && birthrightResult.compliant
    && !birthrightResult.firewall_request_required;

  const canStep1 = form.application && form.environment && form.datacenter;
  const canStep2 = form.src_nh && form.src_sz && form.dst_nh && form.dst_sz;
  const canStep3 = effectivePort && form.protocol;
  const canSubmit = canStep1 && canStep2 && canStep3 && !isBirthrightPermitted;

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setSubmitting(true);
    setDraftCreatedMsg('');
    try {
      const finalSrc = form.src_custom ? autoPrefix(form.src_custom.trim(), 'group') : srcName;
      const finalDst = form.dst_custom ? autoPrefix(form.dst_custom.trim(), 'group') : dstName;
      if (isEditMode && editRule) {
        // Update existing draft rule
        await api.updateRule(editRule.rule_id, {
          application: form.application, environment: form.environment, datacenter: form.datacenter,
          source: { source_type: 'Group', ip_address: null, cidr: null, group_name: finalSrc, ports: effectivePort, neighbourhood: form.src_nh, security_zone: form.src_sz },
          destination: { name: finalDst, security_zone: form.dst_sz, dest_ip: null, ports: effectivePort, is_predefined: false },
          description: form.description,
          source_nh: form.src_nh, destination_nh: form.dst_nh,
          dst_application: form.dst_application || undefined,
        });
        onRuleCreated();
        if (onEditComplete) onEditComplete();
      } else {
        await api.createRule({
          application: form.application, environment: form.environment, datacenter: form.datacenter,
          source: finalSrc, source_zone: form.src_sz,
          destination: finalDst, destination_zone: form.dst_sz,
          port: effectivePort, protocol: form.protocol, action: form.action,
          description: form.description, is_group_to_group: true,
          source_nh: form.src_nh, destination_nh: form.dst_nh,
          dst_application: form.dst_application || undefined,
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

  return (
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
            <div className="grid grid-cols-2 gap-5">
              <div>
                <label className={lbl}>Environment</label>
                <select className={sel} value={form.environment} onChange={e => { upd('environment', e.target.value); upd('src_nh', ''); upd('src_sz', ''); upd('dst_nh', ''); upd('dst_sz', ''); }}>
                  <option value="Production">Production</option>
                  <option value="Non-Production">Non-Production</option>
                  <option value="Pre-Production">Pre-Production</option>
                </select>
              </div>
              <div>
                <label className={lbl}>Datacenter</label>
                <select className={sel} value={form.datacenter} onChange={e => upd('datacenter', e.target.value)}>
                  {datacenters.map(dc => (
                    <option key={dc.code} value={dc.code}>{dc.name}</option>
                  ))}
                </select>
              </div>
            </div>
            {form.application && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <span className="text-sm text-blue-800 font-medium">
                  Building rule: <strong>{form.application}</strong>
                  {form.src_component && <> ({form.src_component})</>}
                  {form.dst_application && form.dst_application !== form.application && (
                    <> &rarr; <strong>{form.dst_application}</strong>{form.dst_component && <> ({form.dst_component})</>}</>
                  )}
                  {' '}in <strong>{form.environment}</strong> at <strong>{datacenters.find(d => d.code === form.datacenter)?.name}</strong>
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
                      <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                        <p className="text-xs text-amber-700 font-medium mb-1">No NGDC groups found for {form.application} in {form.src_nh}/{form.src_sz}</p>
                        <p className="text-[10px] text-amber-600 mb-2">Create one in <strong>App Groups (Manage Groups)</strong> first, or pick a subtype to auto-name:</p>
                        <select className={sel + ' mb-2'} value={form.src_subtype} onChange={e => { upd('src_subtype', e.target.value); upd('src_custom', ''); }}>
                          {SUBTYPES.map(s => (<option key={s.code} value={s.code}>{s.code} - {s.name}</option>))}
                        </select>
                        {srcSuggestedName && (
                          <button onClick={() => upd('src_custom', srcSuggestedName)}
                            className="w-full text-left px-2 py-1.5 text-xs bg-white border border-amber-300 rounded hover:bg-amber-50 transition-colors">
                            Use: <code className="font-mono text-amber-700">{srcSuggestedName}</code>
                          </button>
                        )}
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
                      <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                        <p className="text-xs text-amber-700 font-medium mb-1">No NGDC groups found for {form.dst_application || form.application} in {form.dst_nh}/{form.dst_sz}</p>
                        <p className="text-[10px] text-amber-600 mb-2">Create one in <strong>App Groups (Manage Groups)</strong> first, or pick a subtype to auto-name:</p>
                        <select className={sel + ' mb-2'} value={form.dst_subtype} onChange={e => { upd('dst_subtype', e.target.value); upd('dst_custom', ''); }}>
                          {SUBTYPES.map(s => (<option key={s.code} value={s.code}>{s.code} - {s.name}</option>))}
                        </select>
                        {dstSuggestedName && (
                          <button onClick={() => upd('dst_custom', dstSuggestedName)}
                            className="w-full text-left px-2 py-1.5 text-xs bg-white border border-amber-300 rounded hover:bg-amber-50 transition-colors">
                            Use: <code className="font-mono text-amber-700">{dstSuggestedName}</code>
                          </button>
                        )}
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
}
