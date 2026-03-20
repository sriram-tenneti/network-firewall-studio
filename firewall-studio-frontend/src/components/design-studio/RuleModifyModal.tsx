import { useState, useEffect } from 'react';
import { Modal } from '../shared/Modal';
import type { FirewallRule, RuleDelta } from '@/types';

interface EntryItem {
  id: string;
  type: 'ip' | 'subnet' | 'group';
  value: string;
  isNew?: boolean;
  isModified?: boolean;
}

export interface RuleModification {
  source_entries: EntryItem[];
  destination_entries: EntryItem[];
  ports: string;
  protocol: string;
  action: string;
}

interface RuleModifyModalProps {
  isOpen: boolean;
  onClose: () => void;
  rule: FirewallRule | null;
  onSave: (ruleId: string, changes: RuleModification) => void;
}

function getVal(obj: unknown, key: string): string {
  if (!obj) return '';
  if (typeof obj === 'string') return obj;
  if (typeof obj === 'object' && obj !== null) return (obj as Record<string, string>)[key] || '';
  return '';
}

function detectType(value: string): 'ip' | 'subnet' | 'group' {
  if (value.startsWith('grp-') || value.startsWith('svr-') || value.startsWith('rng-')) return 'group';
  if (value.includes('/')) return 'subnet';
  return 'ip';
}

function parseEntries(obj: unknown): EntryItem[] {
  if (!obj) return [];
  let mainValue = '';
  if (typeof obj === 'string') {
    mainValue = obj;
  } else if (typeof obj === 'object' && obj !== null) {
    const o = obj as Record<string, string>;
    mainValue = o.group_name || o.ip_address || o.cidr || o.name || o.dest_ip || '';
  }
  if (!mainValue) return [];
  return mainValue.split(',').map((v, i) => ({
    id: `entry-${i}`,
    type: detectType(v.trim()),
    value: v.trim(),
  }));
}

function parsePorts(rule: FirewallRule): string {
  const srcPorts = getVal(rule.source, 'ports');
  const dstPorts = getVal(rule.destination, 'ports');
  return srcPorts || dstPorts || '';
}

let nextId = 1;

function EntryEditor({ label, entries, onChange }: {
  label: string;
  entries: EntryItem[];
  onChange: (entries: EntryItem[]) => void;
}) {
  const [addType, setAddType] = useState<'ip' | 'subnet' | 'group'>('ip');
  const [addValue, setAddValue] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');

  const handleAdd = () => {
    if (!addValue.trim()) return;
    const newEntry: EntryItem = {
      id: `new-${nextId++}`,
      type: addType,
      value: addValue.trim(),
      isNew: true,
    };
    onChange([...entries, newEntry]);
    setAddValue('');
  };

  const handleDelete = (id: string) => {
    onChange(entries.filter(e => e.id !== id));
  };

  const handleStartEdit = (entry: EntryItem) => {
    setEditingId(entry.id);
    setEditValue(entry.value);
  };

  const handleSaveEdit = (id: string) => {
    if (!editValue.trim()) return;
    onChange(entries.map(e =>
      e.id === id ? { ...e, value: editValue.trim(), type: detectType(editValue.trim()), isModified: true } : e
    ));
    setEditingId(null);
    setEditValue('');
  };

  const typeColors: Record<string, string> = {
    ip: 'bg-blue-50 text-blue-700 border-blue-200',
    subnet: 'bg-purple-50 text-purple-700 border-purple-200',
    group: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-gray-800">{label}</h4>
        <span className="text-xs text-gray-500">{entries.length} entries</span>
      </div>

      <div className="space-y-1.5 max-h-48 overflow-y-auto">
        {entries.length === 0 && (
          <p className="text-xs text-gray-400 italic py-2">No entries. Add IPs, subnets, or groups below.</p>
        )}
        {entries.map(entry => (
          <div key={entry.id} className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${entry.isNew ? 'bg-green-50 border-green-200' : entry.isModified ? 'bg-amber-50 border-amber-200' : 'bg-white border-gray-200'}`}>
            <span className={`px-1.5 py-0.5 text-[10px] font-bold uppercase rounded border ${typeColors[entry.type]}`}>{entry.type}</span>
            {editingId === entry.id ? (
              <div className="flex-1 flex gap-1.5">
                <input
                  type="text"
                  className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
                  value={editValue}
                  onChange={e => setEditValue(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') handleSaveEdit(entry.id); if (e.key === 'Escape') setEditingId(null); }}
                  autoFocus
                />
                <button onClick={() => handleSaveEdit(entry.id)} className="px-2 py-1 text-xs font-medium text-green-700 bg-green-50 border border-green-200 rounded hover:bg-green-100">Save</button>
                <button onClick={() => setEditingId(null)} className="px-2 py-1 text-xs text-gray-500 hover:text-gray-700">Cancel</button>
              </div>
            ) : (
              <>
                <span className="flex-1 text-sm font-mono text-gray-800">{entry.value}</span>
                {entry.isNew && <span className="text-[10px] text-green-600 font-medium">NEW</span>}
                {entry.isModified && <span className="text-[10px] text-amber-600 font-medium">MODIFIED</span>}
                <button onClick={() => handleStartEdit(entry)} className="px-2 py-0.5 text-xs text-blue-600 hover:bg-blue-50 rounded">Edit</button>
                <button onClick={() => handleDelete(entry.id)} className="px-2 py-0.5 text-xs text-red-600 hover:bg-red-50 rounded">Del</button>
              </>
            )}
          </div>
        ))}
      </div>

      <div className="flex gap-2 pt-1 border-t border-gray-100">
        <select
          value={addType}
          onChange={e => setAddType(e.target.value as 'ip' | 'subnet' | 'group')}
          className="px-2 py-1.5 text-xs font-medium border border-gray-300 rounded-md bg-white"
        >
          <option value="ip">IP Address</option>
          <option value="subnet">Subnet (CIDR)</option>
          <option value="group">Group</option>
        </select>
        <input
          type="text"
          placeholder={addType === 'ip' ? 'e.g. 10.0.1.5' : addType === 'subnet' ? 'e.g. 10.0.1.0/24' : 'e.g. grp-APP01-NH01-STD-web'}
          value={addValue}
          onChange={e => setAddValue(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') handleAdd(); }}
          className="flex-1 px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500"
        />
        <button onClick={handleAdd} disabled={!addValue.trim()} className="px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed">
          + Add
        </button>
      </div>
    </div>
  );
}

export function RuleModifyModal({ isOpen, onClose, rule, onSave }: RuleModifyModalProps) {
  const [sourceEntries, setSourceEntries] = useState<EntryItem[]>([]);
  const [destEntries, setDestEntries] = useState<EntryItem[]>([]);
  const [ports, setPorts] = useState('');
  const [protocol, setProtocol] = useState('TCP');
  const [action, setAction] = useState('Allow');
  const [activeSection, setActiveSection] = useState<'source' | 'destination' | 'service'>('source');

  useEffect(() => {
    if (rule && isOpen) {
      setSourceEntries(parseEntries(rule.source));
      setDestEntries(parseEntries(rule.destination));
      setPorts(parsePorts(rule));
      setProtocol('TCP');
      setAction('Allow');
      setActiveSection('source');
    }
  }, [rule, isOpen]);

  if (!rule) return null;

  const handleSave = () => {
    onSave(rule.rule_id, {
      source_entries: sourceEntries,
      destination_entries: destEntries,
      ports,
      protocol,
      action,
    });
    onClose();
  };

  // Compute full delta for display
  const computeDelta = (): RuleDelta => {
    const delta: RuleDelta = { added: {}, removed: {}, changed: {} };
    const origSrc = parseEntries(rule.source);
    const origDst = parseEntries(rule.destination);
    const origPorts = parsePorts(rule);
    const origSrcVals = new Set(origSrc.map(e => e.value));
    const curSrcVals = new Set(sourceEntries.map(e => e.value));
    const addedSrc = sourceEntries.filter(e => !origSrcVals.has(e.value)).map(e => e.value);
    const removedSrc = origSrc.filter(e => !curSrcVals.has(e.value)).map(e => e.value);
    if (addedSrc.length) delta.added['source'] = addedSrc;
    if (removedSrc.length) delta.removed['source'] = removedSrc;
    const origDstVals = new Set(origDst.map(e => e.value));
    const curDstVals = new Set(destEntries.map(e => e.value));
    const addedDst = destEntries.filter(e => !origDstVals.has(e.value)).map(e => e.value);
    const removedDst = origDst.filter(e => !curDstVals.has(e.value)).map(e => e.value);
    if (addedDst.length) delta.added['destination'] = addedDst;
    if (removedDst.length) delta.removed['destination'] = removedDst;
    const modifiedSrc = sourceEntries.filter(e => e.isModified).map(e => e.value);
    const modifiedDst = destEntries.filter(e => e.isModified).map(e => e.value);
    if (modifiedSrc.length) delta.changed['source_modified'] = { from: 'original', to: modifiedSrc.join(', ') };
    if (modifiedDst.length) delta.changed['destination_modified'] = { from: 'original', to: modifiedDst.join(', ') };
    if (ports !== origPorts) delta.changed['ports'] = { from: origPorts || '(none)', to: ports || '(none)' };
    if (protocol !== 'TCP') delta.changed['protocol'] = { from: 'TCP', to: protocol };
    if (action !== 'Allow') delta.changed['action'] = { from: 'Allow', to: action };
    return delta;
  };
  const currentDelta = computeDelta();
  const hasDeltaChanges = Object.keys(currentDelta.added).length > 0 || Object.keys(currentDelta.removed).length > 0 || Object.keys(currentDelta.changed).length > 0;

  const sectionTabs = [
    { id: 'source' as const, label: 'Source', count: sourceEntries.length },
    { id: 'destination' as const, label: 'Destination', count: destEntries.length },
    { id: 'service' as const, label: 'Service / Ports', count: null },
  ];

  const inputClass = 'w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white';

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Modify Rule: ${rule.rule_id}`} subtitle={`${rule.application} | ${rule.environment}`} size="lg">
      <div className="space-y-4">
        <div className="flex border-b border-gray-200">
          {sectionTabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveSection(tab.id)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${activeSection === tab.id ? 'border-blue-600 text-blue-700' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
            >
              {tab.label}
              {tab.count !== null && <span className="ml-1.5 px-1.5 py-0.5 text-[10px] font-bold bg-gray-100 text-gray-600 rounded-full">{tab.count}</span>}
            </button>
          ))}
        </div>

        {activeSection === 'source' && (
          <EntryEditor label="Source Entries" entries={sourceEntries} onChange={setSourceEntries} />
        )}

        {activeSection === 'destination' && (
          <EntryEditor label="Destination Entries" entries={destEntries} onChange={setDestEntries} />
        )}

        {activeSection === 'service' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Ports</label>
              <input className={inputClass} placeholder="e.g. 443, 8080-8090, 80,443" value={ports} onChange={e => setPorts(e.target.value)} />
              <p className="text-xs text-gray-400 mt-1">Comma-separated ports or ranges (e.g. 80,443,8080-8090)</p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Protocol</label>
                <select className={inputClass} value={protocol} onChange={e => setProtocol(e.target.value)}>
                  <option value="TCP">TCP</option>
                  <option value="UDP">UDP</option>
                  <option value="ICMP">ICMP</option>
                  <option value="ANY">ANY</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Action</label>
                <select className={inputClass} value={action} onChange={e => setAction(e.target.value)}>
                  <option value="Allow">Allow</option>
                  <option value="Deny">Deny</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Full Delta View - Always Visible */}
        <div className={`border rounded-lg p-3 ${hasDeltaChanges ? 'border-blue-200 bg-blue-50' : 'border-gray-200 bg-gray-50'}`}>
          <h4 className={`text-sm font-semibold mb-2 ${hasDeltaChanges ? 'text-blue-800' : 'text-gray-500'}`}>
            Change Delta {hasDeltaChanges ? '' : '(No changes yet)'}
          </h4>
          {hasDeltaChanges ? (
            <div className="space-y-2">
              {Object.keys(currentDelta.added).length > 0 && (
                <div>
                  <h5 className="text-xs font-semibold text-green-700 mb-1">Added</h5>
                  {Object.entries(currentDelta.added).map(([field, values]) => (
                    <div key={field} className="ml-2">
                      <span className="text-xs text-gray-500">{field}:</span>
                      {values.map((v, i) => (
                        <div key={i} className="text-xs text-green-700 font-mono ml-2">+ {v}</div>
                      ))}
                    </div>
                  ))}
                </div>
              )}
              {Object.keys(currentDelta.removed).length > 0 && (
                <div>
                  <h5 className="text-xs font-semibold text-red-700 mb-1">Removed</h5>
                  {Object.entries(currentDelta.removed).map(([field, values]) => (
                    <div key={field} className="ml-2">
                      <span className="text-xs text-gray-500">{field}:</span>
                      {values.map((v, i) => (
                        <div key={i} className="text-xs text-red-700 font-mono ml-2">- {v}</div>
                      ))}
                    </div>
                  ))}
                </div>
              )}
              {Object.keys(currentDelta.changed).length > 0 && (
                <div>
                  <h5 className="text-xs font-semibold text-blue-700 mb-1">Changed</h5>
                  {Object.entries(currentDelta.changed).map(([field, change]) => (
                    <div key={field} className="ml-2 text-xs">
                      <span className="text-gray-500">{field.replace(/_/g, ' ')}:</span>
                      <span className="text-red-600 line-through ml-1">{change.from}</span>
                      <span className="mx-1">&rarr;</span>
                      <span className="text-green-600">{change.to}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <p className="text-xs text-gray-400 italic">Make changes to source, destination, or service to see the delta here.</p>
          )}
        </div>
      </div>

      <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
        <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
        <button onClick={handleSave} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700">
          Save Changes
        </button>
      </div>
    </Modal>
  );
}
