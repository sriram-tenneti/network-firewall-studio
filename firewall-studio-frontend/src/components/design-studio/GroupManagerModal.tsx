import { useState, useEffect } from 'react';
import { Modal } from '../shared/Modal';
import { getGroups, createGroup, addGroupMember, removeGroupMember, getAppDCMappings, getAffectedRules, submitGroupPolicyChanges } from '@/lib/api';
import type { FirewallGroup, GroupMember } from '@/types';
import { autoPrefix } from '@/lib/utils';

interface GroupManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
  appId?: string;
  applications?: { app_id: string; app_distributed_id?: string; name: string }[];
  environment?: string;
}

export function GroupManagerModal({ isOpen, onClose, appId, applications = [], environment }: GroupManagerModalProps) {
  const [groups, setGroups] = useState<FirewallGroup[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<FirewallGroup | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(false);
  const [filterAppId, setFilterAppId] = useState(appId || '');
  const [filterEnv, setFilterEnv] = useState(environment || '');
  const [searchQuery, setSearchQuery] = useState('');
  const [newGroup, setNewGroup] = useState({ app_id: appId || '', dc: '', nh: '', sz: '', subtype: '', customSuffix: '', description: '', environment: environment || 'Production' });
  const [createValidationError, setCreateValidationError] = useState<string | null>(null);
  const [newMember, setNewMember] = useState({ type: 'ip' as GroupMember['type'], value: '', description: '' });

  // Policy change tracking — when group members change, affected rules need review
  const [affectedRulesCount, setAffectedRulesCount] = useState(0);
  const [pendingChanges, setPendingChanges] = useState<{ type: string; detail: string; delta?: Record<string, unknown> }[]>([]);
  const [submittingPolicy, setSubmittingPolicy] = useState(false);
  const [policySubmitResult, setPolicySubmitResult] = useState<string | null>(null);

  // Inline members for group creation (Issue #5)
  const [createMembers, setCreateMembers] = useState<{ type: GroupMember['type']; value: string; description: string }[]>([]);
  const [createMemberType, setCreateMemberType] = useState<GroupMember['type']>('ip');
  const [createMemberValue, setCreateMemberValue] = useState('');
  const [createMemberDesc, setCreateMemberDesc] = useState('');

  // App DC mappings for auto-populating NH/SZ dropdowns
  const [allAppDCMappings, setAllAppDCMappings] = useState<Record<string, unknown>[]>([]);
  const [appNHOptions, setAppNHOptions] = useState<string[]>([]);
  const [appSZOptions, setAppSZOptions] = useState<string[]>([]);
  const [appDCOptions, setAppDCOptions] = useState<string[]>([]);
  const [appComponentOptions, setAppComponentOptions] = useState<string[]>([]);

  useEffect(() => {
    if (isOpen) {
      setFilterAppId(appId || '');
      setFilterEnv(environment || '');
      loadGroups(appId || '', environment || '');
      loadAppDCMappings();
    }
  }, [isOpen, appId, environment]);

  const loadAppDCMappings = async () => {
    try {
      const mappings = await getAppDCMappings();
      setAllAppDCMappings(mappings);
      // If we have an initial app, populate its options
      if (appId) updateAppOptions(appId, mappings);
    } catch { /* ignore */ }
  };

  // Resolve app_distributed_id or app_id to matching app_dc_mappings rows
  const getAppMappings = (selectedAppId: string, mappings?: Record<string, unknown>[]) => {
    const source = mappings || allAppDCMappings;
    const resolvedAppId = (() => {
      const app = applications.find(a => (a.app_distributed_id || a.app_id) === selectedAppId);
      return app ? app.app_id : selectedAppId;
    })();
    return source.filter(m => {
      const mDistId = String(m.app_distributed_id || '');
      const mAppId = String(m.app_id || '');
      return mDistId === selectedAppId || mAppId === selectedAppId || mAppId === resolvedAppId || mDistId === resolvedAppId;
    });
  };

  const updateAppOptions = (selectedAppId: string, mappings?: Record<string, unknown>[]) => {
    const appMappings = getAppMappings(selectedAppId, mappings);
    const nhs = [...new Set(appMappings.map(m => String(m.nh || '')).filter(Boolean))].sort();
    // SZ starts with all SZs for the app; will be narrowed when component is selected
    const szs = [...new Set(appMappings.map(m => String(m.sz || '')).filter(Boolean))].sort();
    const dcs = [...new Set(appMappings.map(m => String(m.dc || '')).filter(Boolean))].sort();
    // Extract available components from mappings
    const comps = [...new Set(appMappings.map(m => String(m.component || '')).filter(Boolean))].sort();
    setAppNHOptions(nhs);
    setAppSZOptions(szs);
    setAppDCOptions(dcs);
    setAppComponentOptions(comps);
    // Auto-select first option if available
    setNewGroup(prev => ({
      ...prev,
      app_id: selectedAppId,
      nh: nhs.length === 1 ? nhs[0] : '',
      sz: '',  // Reset SZ — user must pick component first
      subtype: '',  // Reset component
    }));
  };

  // When component changes, filter SZ options to only those mapped for that app+component
  const updateSZForComponent = (component: string) => {
    if (!component || !newGroup.app_id) {
      // No component selected — show all SZs for the app
      const appMappings = getAppMappings(newGroup.app_id);
      const szs = [...new Set(appMappings.map(m => String(m.sz || '')).filter(Boolean))].sort();
      setAppSZOptions(szs);
      return;
    }
    const appMappings = getAppMappings(newGroup.app_id);
    const compMappings = appMappings.filter(m => String(m.component || '') === component);
    const szs = [...new Set(compMappings.map(m => String(m.sz || '')).filter(Boolean))].sort();
    setAppSZOptions(szs);
    // Auto-select SZ if only one option
    setNewGroup(prev => ({
      ...prev,
      subtype: component,
      sz: szs.length === 1 ? szs[0] : '',
    }));
  };

  const loadGroups = async (forAppId?: string, forEnv?: string) => {
    setLoading(true);
    try {
      const data = await getGroups(forAppId || undefined);
      // Client-side environment filter since backend groups may have environment field
      const filtered = forEnv ? data.filter(g => {
        const gEnv = (g as unknown as Record<string, string>).environment;
        return !gEnv || gEnv === forEnv;
      }) : data;
      setGroups(filtered);
    } catch { /* ignore */ }
    setLoading(false);
  };

  const handleAppFilterChange = (newAppId: string) => {
    setFilterAppId(newAppId);
    setSelectedGroup(null);
    loadGroups(newAppId, filterEnv);
    setNewGroup(prev => ({ ...prev, app_id: newAppId }));
    // Also update NH/SZ options when filter app changes
    if (newAppId) updateAppOptions(newAppId);
  };

  const handleEnvFilterChange = (newEnv: string) => {
    setFilterEnv(newEnv);
    setSelectedGroup(null);
    loadGroups(filterAppId, newEnv);
    setNewGroup(prev => ({ ...prev, environment: newEnv || 'Production' }));
  };

  const filteredGroups = groups.filter(g => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return g.name.toLowerCase().includes(q) || g.app_id.toLowerCase().includes(q) || g.description.toLowerCase().includes(q) || (g.members || []).some(m => m.value.toLowerCase().includes(q));
  });

  const handleAddCreateMember = () => {
    if (!createMemberValue.trim()) return;
    const prefixed = autoPrefix(createMemberValue.trim(), createMemberType);
    setCreateMembers(prev => [...prev, { type: createMemberType, value: prefixed, description: createMemberDesc }]);
    setCreateMemberValue('');
    setCreateMemberDesc('');
  };

  const handleRemoveCreateMember = (idx: number) => {
    setCreateMembers(prev => prev.filter((_, i) => i !== idx));
  };

  // Auto-generate group name from standard fields: grp-{APP}-{NH}-{SZ}-{Component}[-{suffix}]
  const autoGroupName = (() => {
    const parts = ['grp', newGroup.app_id, newGroup.nh, newGroup.sz, newGroup.subtype].filter(Boolean);
    if (parts.length < 5) return ''; // All 4 fields required (grp + 4)
    let name = parts.join('-');
    if (newGroup.customSuffix.trim()) name += `-${newGroup.customSuffix.trim()}`;
    return name;
  })();

  // Validation: all required fields + at least 1 member
  const canCreateGroup = !!(newGroup.app_id && newGroup.nh && newGroup.sz && newGroup.subtype && createMembers.length > 0 && autoGroupName);

  const handleCreateGroup = async () => {
    if (!newGroup.app_id) { setCreateValidationError('Application is required'); return; }
    if (!newGroup.nh) { setCreateValidationError('Neighbourhood (NH) is required'); return; }
    if (!newGroup.sz) { setCreateValidationError('Security Zone (SZ) is required'); return; }
    if (!newGroup.subtype) { setCreateValidationError('Component is required'); return; }
    if (createMembers.length === 0) { setCreateValidationError('At least one member (IP/subnet/group) is required — empty groups are not allowed'); return; }
    setCreateValidationError(null);
    try {
      const prefixedGroup = {
        ...newGroup,
        name: autoGroupName,
        members: createMembers.map(m => ({ type: m.type, value: m.value, description: m.description })),
      };
      await createGroup(prefixedGroup);
      setShowCreate(false);
      setNewGroup({ app_id: filterAppId || '', dc: '', nh: '', sz: '', subtype: '', customSuffix: '', description: '', environment: filterEnv || 'Production' });
      setCreateMembers([]);
      setCreateValidationError(null);
      loadGroups(filterAppId, filterEnv);
    } catch { setCreateValidationError('Failed to create group — check for duplicates'); }
  };

  const handleAddMember = async () => {
    if (!selectedGroup || !newMember.value) return;
    try {
      const prefixedMember = { ...newMember, value: autoPrefix(newMember.value, newMember.type) };
      const updated = await addGroupMember(selectedGroup.name, prefixedMember);
      setSelectedGroup(updated);
      setNewMember({ type: 'ip', value: '', description: '' });
      loadGroups();
      // Track this as a pending policy change
      const delta = { added: { [`group:${selectedGroup.name}`]: [prefixedMember.value] }, removed: {}, changed: {} };
      setPendingChanges(prev => [...prev, { type: 'member_added', detail: `Added ${prefixedMember.value}`, delta }]);
      // Check affected rules count
      try { const res = await getAffectedRules(selectedGroup.name); setAffectedRulesCount(res.affected_rules); } catch { /* ignore */ }
    } catch { /* ignore */ }
  };

  const handleRemoveMember = async (memberValue: string) => {
    if (!selectedGroup) return;
    try {
      const updated = await removeGroupMember(selectedGroup.name, memberValue);
      setSelectedGroup(updated);
      loadGroups();
      // Track this as a pending policy change
      const delta = { added: {}, removed: { [`group:${selectedGroup.name}`]: [memberValue] }, changed: {} };
      setPendingChanges(prev => [...prev, { type: 'member_removed', detail: `Removed ${memberValue}`, delta }]);
      // Check affected rules count
      try { const res = await getAffectedRules(selectedGroup.name); setAffectedRulesCount(res.affected_rules); } catch { /* ignore */ }
    } catch { /* ignore */ }
  };

  const handleSubmitPolicyChanges = async () => {
    if (!selectedGroup || pendingChanges.length === 0) return;
    setSubmittingPolicy(true);
    try {
      // Merge all pending deltas
      const mergedDelta: Record<string, unknown> = { added: {} as Record<string, string[]>, removed: {} as Record<string, string[]>, changed: {} };
      for (const pc of pendingChanges) {
        if (pc.delta) {
          const d = pc.delta as { added?: Record<string, string[]>; removed?: Record<string, string[]> };
          for (const [k, v] of Object.entries(d.added || {})) {
            (mergedDelta.added as Record<string, string[]>)[k] = [...((mergedDelta.added as Record<string, string[]>)[k] || []), ...v];
          }
          for (const [k, v] of Object.entries(d.removed || {})) {
            (mergedDelta.removed as Record<string, string[]>)[k] = [...((mergedDelta.removed as Record<string, string[]>)[k] || []), ...v];
          }
        }
      }
      const changeDetails = pendingChanges.map(c => c.detail).join('; ');
      const result = await submitGroupPolicyChanges(selectedGroup.name, 'group_member_change', changeDetails, mergedDelta);
      setPolicySubmitResult(`Submitted ${result.affected_rules} rule(s) for policy review`);
      setPendingChanges([]);
      setAffectedRulesCount(0);
    } catch {
      setPolicySubmitResult('Failed to submit policy changes');
    } finally {
      setSubmittingPolicy(false);
      setTimeout(() => setPolicySubmitResult(null), 5000);
    }
  };

  const inputClass = 'w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500';

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Group Management" subtitle={[filterEnv, filterAppId].filter(Boolean).join(' | ') || 'All Environments & Applications'} size="xl">
      <div className="flex gap-4 min-h-[400px]">
        {/* Left panel - Group list */}
        <div className="w-1/3 border-r pr-4">
          {/* Environment filter */}
          <div className="mb-2">
            <select
              value={filterEnv}
              onChange={e => handleEnvFilterChange(e.target.value)}
              className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded-md bg-white focus:ring-1 focus:ring-blue-500"
            >
              <option value="">All Environments</option>
              <option value="Production">Production</option>
              <option value="Non-Production">Non-Production</option>
              <option value="Pre-Production">Pre-Production</option>
            </select>
          </div>
          {/* App Distributed Id filter */}
          <div className="mb-3">
            <select
              value={filterAppId}
              onChange={e => handleAppFilterChange(e.target.value)}
              className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded-md bg-white focus:ring-1 focus:ring-blue-500"
            >
              <option value="">All Applications</option>
              {applications.map(app => (
                <option key={app.app_distributed_id || app.app_id} value={app.app_distributed_id || app.app_id}>{app.app_distributed_id || app.app_id}</option>
              ))}
            </select>
          </div>
          {/* Search within groups */}
          <div className="mb-3">
            <input
              type="text"
              placeholder="Search groups, IPs, subnets..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-700">Groups ({filteredGroups.length})</h3>
            <button onClick={() => setShowCreate(!showCreate)} className="text-xs text-blue-600 hover:text-blue-800 font-medium">
              {showCreate ? 'Cancel' : '+ New'}
            </button>
          </div>

          {showCreate && (
            <div className="mb-3 p-3 bg-blue-50 rounded-lg space-y-2">
              {/* Standards notice */}
              <div className="p-2 bg-blue-100 border border-blue-200 rounded text-[10px] text-blue-800">
                <strong>NGDC Naming Standard:</strong> Group name is auto-generated as <span className="font-mono">grp-APP-NH-SZ-Component</span>. All fields are mandatory. At least one member is required.
              </div>
              <div>
                <label className="text-xs text-gray-500">Application <span className="text-red-500">*</span></label>
                <select className={inputClass} value={newGroup.app_id} onChange={e => { setNewGroup({ ...newGroup, app_id: e.target.value, dc: '', nh: '', sz: '', subtype: '', customSuffix: '' }); updateAppOptions(e.target.value); setCreateValidationError(null); }}>
                  <option value="">-- Select Application --</option>
                  {applications.map(app => (
                    <option key={app.app_distributed_id || app.app_id} value={app.app_distributed_id || app.app_id}>{app.app_distributed_id || app.app_id}</option>
                  ))}
                </select>
                {newGroup.app_id && appDCOptions.length > 0 && (
                  <p className="text-[9px] text-gray-500 mt-0.5">DCs: {appDCOptions.join(', ')} (group applies to all mapped DCs)</p>
                )}
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="text-xs text-gray-500">NH <span className="text-red-500">*</span></label>
                  <select className={inputClass} value={newGroup.nh} onChange={e => { setNewGroup({ ...newGroup, nh: e.target.value }); setCreateValidationError(null); }} disabled={!newGroup.app_id}>
                    <option value="">-- Select NH --</option>
                    {appNHOptions.map(nh => <option key={nh} value={nh}>{nh}</option>)}
                  </select>
                  {!newGroup.app_id && <p className="text-[9px] text-gray-400 mt-0.5">Select an app first</p>}
                  {newGroup.app_id && appNHOptions.length === 0 && <p className="text-[9px] text-amber-600 mt-0.5">No NHs mapped for this app</p>}
                </div>
                <div>
                  <label className="text-xs text-gray-500">SZ <span className="text-red-500">*</span></label>
                  <select className={inputClass} value={newGroup.sz} onChange={e => { setNewGroup({ ...newGroup, sz: e.target.value }); setCreateValidationError(null); }} disabled={!newGroup.app_id}>
                    <option value="">-- Select SZ --</option>
                    {appSZOptions.map(sz => <option key={sz} value={sz}>{sz}</option>)}
                  </select>
                  {!newGroup.app_id && <p className="text-[9px] text-gray-400 mt-0.5">Select an app first</p>}
                  {newGroup.app_id && appSZOptions.length === 0 && <p className="text-[9px] text-amber-600 mt-0.5">No SZs mapped for this app</p>}
                </div>
                <div>
                  <label className="text-xs text-gray-500">Component <span className="text-red-500">*</span></label>
                  <select className={inputClass} value={newGroup.subtype} onChange={e => { updateSZForComponent(e.target.value); setCreateValidationError(null); }} disabled={!newGroup.app_id}>
                    <option value="">-- Select Component --</option>
                    {appComponentOptions.length > 0
                      ? appComponentOptions.map(c => <option key={c} value={c}>{c}</option>)
                      : ['WEB','APP','DB','MQ','BAT','API'].map(c => <option key={c} value={c}>{c}</option>)
                    }
                  </select>
                  {!newGroup.app_id && <p className="text-[9px] text-gray-400 mt-0.5">Select an app first</p>}
                  {newGroup.subtype && appSZOptions.length > 0 && <p className="text-[9px] text-green-600 mt-0.5">SZ filtered for {newGroup.subtype}</p>}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-xs text-gray-500">Custom Suffix <span className="text-gray-400">(optional)</span></label>
                  <input className={inputClass} placeholder="e.g. frontend, batch01" value={newGroup.customSuffix} onChange={e => setNewGroup({ ...newGroup, customSuffix: e.target.value.replace(/[^a-zA-Z0-9_-]/g, '') })} />
                  <p className="text-[9px] text-gray-400 mt-0.5">For sub-component differentiation only</p>
                </div>
                <div>
                  <label className="text-xs text-gray-500">Environment</label>
                  <select className={inputClass} value={newGroup.environment} onChange={e => setNewGroup({ ...newGroup, environment: e.target.value })}>
                    <option value="Production">Production</option>
                    <option value="Non-Production">Non-Production</option>
                    <option value="Pre-Production">Pre-Production</option>
                  </select>
                </div>
              </div>
              {/* Auto-generated group name preview */}
              <div className={`rounded px-2 py-1.5 text-xs font-mono ${autoGroupName ? 'bg-green-50 border border-green-200 text-green-800' : 'bg-gray-100 border border-gray-200 text-gray-400'}`}>
                {autoGroupName || 'grp-{APP}-{NH}-{SZ}-{Component} — select all required fields'}
              </div>
              <input className={inputClass} placeholder="Description" value={newGroup.description} onChange={e => setNewGroup({ ...newGroup, description: e.target.value })} />
              {/* Inline member creation during group creation — REQUIRED */}
              <div className={`border rounded-md p-2 ${createMembers.length === 0 ? 'border-red-300 bg-red-50' : 'border-gray-200 bg-white'}`}>
                <div className="text-[10px] font-semibold uppercase mb-1 flex items-center gap-1">
                  <span className={createMembers.length === 0 ? 'text-red-600' : 'text-gray-500'}>Members <span className="text-red-500">*</span> (at least 1 required)</span>
                  {createMembers.length > 0 && <span className="text-green-600">({createMembers.length} added)</span>}
                </div>
                {createMembers.length > 0 && (
                  <div className="space-y-1 mb-2 max-h-24 overflow-y-auto">
                    {createMembers.map((m, i) => (
                      <div key={i} className="flex items-center gap-1 px-2 py-1 bg-gray-50 rounded text-xs">
                        <span className={`px-1 py-0.5 text-[9px] font-bold uppercase rounded ${
                          m.type === 'ip' ? 'bg-blue-100 text-blue-700' :
                          m.type === 'cidr' ? 'bg-green-100 text-green-700' :
                          m.type === 'range' ? 'bg-amber-100 text-amber-700' :
                          'bg-purple-100 text-purple-700'
                        }`}>{m.type}</span>
                        <span className="flex-1 font-mono text-gray-700 truncate">{m.value}</span>
                        <button onClick={() => handleRemoveCreateMember(i)} className="text-red-500 hover:text-red-700 text-[10px] font-medium">Remove</button>
                      </div>
                    ))}
                  </div>
                )}
                <div className="flex gap-1">
                  <select className="px-1.5 py-1 border border-gray-300 rounded text-[10px]" value={createMemberType} onChange={e => setCreateMemberType(e.target.value as GroupMember['type'])}>
                    <option value="ip">IP</option>
                    <option value="cidr">CIDR</option>
                    <option value="range">Range</option>
                    <option value="group">Group</option>
                  </select>
                  <input className="flex-1 px-1.5 py-1 border border-gray-300 rounded text-[10px]" placeholder={createMemberType === 'cidr' ? '10.0.1.0/24' : createMemberType === 'range' ? '10.0.1.1-10.0.1.50' : createMemberType === 'group' ? 'grp-name' : '10.0.1.1'} value={createMemberValue} onChange={e => setCreateMemberValue(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') handleAddCreateMember(); }} />
                  <input className="w-20 px-1.5 py-1 border border-gray-300 rounded text-[10px]" placeholder="Desc" value={createMemberDesc} onChange={e => setCreateMemberDesc(e.target.value)} />
                  <button onClick={handleAddCreateMember} disabled={!createMemberValue.trim()} className="px-2 py-1 text-[10px] font-medium text-white bg-green-600 rounded hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed whitespace-nowrap">+</button>
                </div>
              </div>
              {createValidationError && (
                <div className="p-2 bg-red-50 border border-red-200 rounded text-[10px] text-red-700 font-medium">
                  {createValidationError}
                </div>
              )}
              <button onClick={handleCreateGroup} disabled={!canCreateGroup} className={`w-full px-3 py-1.5 text-xs font-medium text-white rounded-md ${canCreateGroup ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-300 cursor-not-allowed'}`}>
                {canCreateGroup ? `Create Group "${autoGroupName}" with ${createMembers.length} member${createMembers.length > 1 ? 's' : ''}` : 'Complete all required fields & add members'}
              </button>
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
            </div>
          ) : (
            <div className="space-y-1 max-h-[280px] overflow-y-auto">
              {filteredGroups.map(g => (
                <button
                  key={g.name}
                  onClick={() => setSelectedGroup(g)}
                  className={`w-full text-left p-2 rounded-md text-xs transition-colors ${
                    selectedGroup?.name === g.name ? 'bg-blue-100 text-blue-800 border border-blue-300' : 'hover:bg-gray-50 border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-1.5">
                    <span className="font-medium truncate">{g.name}</span>
                    {(g as unknown as Record<string, unknown>).type === 'migration' && (
                      <span className="flex-shrink-0 px-1 py-0.5 text-[8px] font-bold uppercase rounded bg-emerald-100 text-emerald-700">migrated</span>
                    )}
                  </div>
                  <div className="text-gray-500 mt-0.5 flex items-center gap-2">
                    <span>{g.members?.length || 0} members</span>
                    {g.nh && <span className="text-gray-400">NH: {g.nh}</span>}
                    {g.sz && <span className="text-gray-400">SZ: {g.sz}</span>}
                  </div>
                </button>
              ))}
              {groups.length === 0 && <p className="text-xs text-gray-400 text-center py-4">No groups found</p>}
            </div>
          )}
        </div>

        {/* Right panel - Group details */}
        <div className="flex-1 pl-2">
          {selectedGroup ? (
            <>
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-gray-800">{selectedGroup.name}</h3>
                <p className="text-xs text-gray-500 mt-1">{selectedGroup.description}</p>
                <div className="flex gap-3 mt-2 text-xs text-gray-500">
                  <span>App: {selectedGroup.app_id}</span>
                  {(selectedGroup as unknown as Record<string, string>).dc && <span>DC: {(selectedGroup as unknown as Record<string, string>).dc}</span>}
                  <span>NH: {selectedGroup.nh}</span>
                  <span>SZ: {selectedGroup.sz}</span>
                  <span>Component: {selectedGroup.subtype}</span>
                </div>
              </div>

              {/* Add member form */}
              <div className="flex gap-2 mb-3">
                <select className="px-2 py-1.5 border border-gray-300 rounded-md text-xs" value={newMember.type} onChange={e => setNewMember({ ...newMember, type: e.target.value as GroupMember['type'] })}>
                  <option value="ip">IP Address</option>
                  <option value="cidr">Subnet (CIDR)</option>
                  <option value="range">IP Range</option>
                  <option value="group">Nested Group</option>
                </select>
                <input className="flex-1 px-2 py-1.5 border border-gray-300 rounded-md text-xs" placeholder={newMember.type === 'cidr' ? '10.0.1.0/24' : newMember.type === 'range' ? '10.0.1.1-10.0.1.50' : '10.0.1.1'} value={newMember.value} onChange={e => setNewMember({ ...newMember, value: e.target.value })} />
                <input className="w-32 px-2 py-1.5 border border-gray-300 rounded-md text-xs" placeholder="Description" value={newMember.description} onChange={e => setNewMember({ ...newMember, description: e.target.value })} />
                <button onClick={handleAddMember} className="px-3 py-1.5 text-xs font-medium text-white bg-green-600 rounded-md hover:bg-green-700 whitespace-nowrap">Add</button>
              </div>

              {/* Members list */}
              <div className="border rounded-lg overflow-hidden">
                <table className="w-full text-xs">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">Type</th>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">Value</th>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">Description</th>
                      <th className="px-3 py-2 text-right font-medium text-gray-600">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {(selectedGroup.members || []).map((m, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        <td className="px-3 py-2">
                          <span className={`inline-flex px-1.5 py-0.5 rounded text-xs font-medium ${
                            m.type === 'ip' ? 'bg-blue-100 text-blue-700' :
                            m.type === 'cidr' ? 'bg-green-100 text-green-700' :
                            m.type === 'range' ? 'bg-amber-100 text-amber-700' :
                            'bg-purple-100 text-purple-700'
                          }`}>
                            {m.type.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-3 py-2 font-mono">{m.value}</td>
                        <td className="px-3 py-2 text-gray-500">{m.description}</td>
                        <td className="px-3 py-2 text-right">
                          <button onClick={() => handleRemoveMember(m.value)} className="text-red-500 hover:text-red-700 font-medium">Remove</button>
                        </td>
                      </tr>
                    ))}
                    {(!selectedGroup.members || selectedGroup.members.length === 0) && (
                      <tr><td colSpan={4} className="px-3 py-4 text-center text-gray-400">No members in this group</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-sm text-gray-400">
              Select a group to view and manage its members
            </div>
          )}
        </div>
      </div>

      {/* Policy change notification bar */}
      {pendingChanges.length > 0 && affectedRulesCount > 0 && (
        <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-amber-800">
                {pendingChanges.length} group change(s) affect {affectedRulesCount} rule(s)
              </p>
              <p className="text-xs text-amber-600 mt-0.5">
                Submit for policy review to ensure affected rules are reviewed, approved, and compiled.
              </p>
              <ul className="mt-1 text-xs text-amber-700 list-disc list-inside">
                {pendingChanges.map((pc, i) => <li key={i}>{pc.detail}</li>)}
              </ul>
            </div>
            <button
              onClick={handleSubmitPolicyChanges}
              disabled={submittingPolicy}
              className="px-4 py-2 text-xs font-medium text-white bg-amber-600 rounded-md hover:bg-amber-700 disabled:bg-gray-300 disabled:cursor-not-allowed whitespace-nowrap ml-4"
            >
              {submittingPolicy ? 'Submitting...' : 'Submit for Policy Review'}
            </button>
          </div>
        </div>
      )}
      {policySubmitResult && (
        <div className={`mt-2 p-2 rounded text-xs font-medium ${policySubmitResult.includes('Failed') ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
          {policySubmitResult}
        </div>
      )}

      <div className="flex justify-end mt-4 pt-4 border-t">
        <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">Close</button>
      </div>
    </Modal>
  );
}
