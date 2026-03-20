import { useState, useEffect, useCallback } from 'react';
import type { Application } from '@/types';
import { getNeighbourhoods, getSecurityZones, getGroups, createRule } from '@/lib/api';

interface DragDropRuleBuilderProps {
  applications: Application[];
  onRuleCreated: () => void;
}

interface FlowNode {
  id: string;
  type: 'source' | 'policy' | 'destination' | 'action' | 'zone';
  label: string;
  value: string;
  x: number;
  y: number;
}

interface FlowConnection {
  from: string;
  to: string;
}

interface NHOption { nh_id: string; name: string }
interface SZOption { code: string; name: string }

const FLOW_TEMPLATES = [
  { label: 'Source Group', type: 'source' as const, icon: 'GRP', prefix: 'grp-', color: 'blue' },
  { label: 'Source IP', type: 'source' as const, icon: 'SVR', prefix: 'svr-', color: 'blue' },
  { label: 'Source Range', type: 'source' as const, icon: 'RNG', prefix: 'rng-', color: 'blue' },
  { label: 'Source Subnet', type: 'source' as const, icon: 'NET', prefix: '', color: 'blue' },
  { label: 'Security Zone', type: 'zone' as const, icon: 'SZ', prefix: '', color: 'teal' },
  { label: 'Policy Check', type: 'policy' as const, icon: 'POL', prefix: 'policy', color: 'amber' },
  { label: 'Dest Group', type: 'destination' as const, icon: 'GRP', prefix: 'grp-', color: 'emerald' },
  { label: 'Dest IP', type: 'destination' as const, icon: 'SVR', prefix: 'svr-', color: 'emerald' },
  { label: 'Allow', type: 'action' as const, icon: 'OK', prefix: 'allow', color: 'green' },
  { label: 'Deny', type: 'action' as const, icon: 'X', prefix: 'deny', color: 'red' },
];

const COLOR_MAP: Record<string, { bg: string; border: string; text: string; icon: string }> = {
  blue: { bg: 'bg-blue-50', border: 'border-blue-300', text: 'text-blue-800', icon: 'bg-blue-200 text-blue-700' },
  teal: { bg: 'bg-teal-50', border: 'border-teal-300', text: 'text-teal-800', icon: 'bg-teal-200 text-teal-700' },
  amber: { bg: 'bg-amber-50', border: 'border-amber-300', text: 'text-amber-800', icon: 'bg-amber-200 text-amber-700' },
  emerald: { bg: 'bg-emerald-50', border: 'border-emerald-300', text: 'text-emerald-800', icon: 'bg-emerald-200 text-emerald-700' },
  green: { bg: 'bg-green-50', border: 'border-green-300', text: 'text-green-800', icon: 'bg-green-200 text-green-700' },
  red: { bg: 'bg-red-50', border: 'border-red-300', text: 'text-red-800', icon: 'bg-red-200 text-red-700' },
};

const SERVICE_PRESETS = [
  { label: 'HTTPS (443/TCP)', port: '443', protocol: 'TCP' },
  { label: 'HTTP (80/TCP)', port: '80', protocol: 'TCP' },
  { label: 'SSH (22/TCP)', port: '22', protocol: 'TCP' },
  { label: 'SQL Server (1433/TCP)', port: '1433', protocol: 'TCP' },
  { label: 'Oracle (1521/TCP)', port: '1521', protocol: 'TCP' },
  { label: 'MySQL (3306/TCP)', port: '3306', protocol: 'TCP' },
  { label: 'PostgreSQL (5432/TCP)', port: '5432', protocol: 'TCP' },
  { label: 'RDP (3389/TCP)', port: '3389', protocol: 'TCP' },
  { label: 'DNS (53/UDP)', port: '53', protocol: 'UDP' },
  { label: 'ICMP', port: '', protocol: 'ICMP' },
  { label: 'Custom', port: '', protocol: 'TCP' },
];

export function DragDropRuleBuilder({ applications, onRuleCreated }: DragDropRuleBuilderProps) {
  const [nodes, setNodes] = useState<FlowNode[]>([]);
  const [connections, setConnections] = useState<FlowConnection[]>([]);
  const [dragItem, setDragItem] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [editLabel, setEditLabel] = useState('');
  const [editValue, setEditValue] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [neighbourhoods, setNeighbourhoods] = useState<NHOption[]>([]);
  const [securityZones, setSecurityZones] = useState<SZOption[]>([]);
  const [appGroups, setAppGroups] = useState<{ name: string; members: { value: string }[] }[]>([]);
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    application: '',
    environment: 'Production',
    datacenter: 'ALPHA_NGDC',
    source: '',
    source_zone: '',
    destination: '',
    destination_zone: '',
    port: '443',
    protocol: 'TCP',
    action: 'Allow',
    nh: '',
    sz: '',
    description: '',
  });

  const loadRefData = useCallback(async () => {
    try {
      const [nhs, szs] = await Promise.all([getNeighbourhoods(), getSecurityZones()]);
      setNeighbourhoods(nhs as unknown as NHOption[]);
      setSecurityZones(szs as unknown as SZOption[]);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { loadRefData(); }, [loadRefData]);

  const loadAppGroups = useCallback(async (appId: string) => {
    if (!appId) return;
    try {
      const groups = await getGroups(appId);
      setAppGroups(groups as unknown as { name: string; members: { value: string }[] }[]);
    } catch { setAppGroups([]); }
  }, []);

  useEffect(() => { if (formData.application) loadAppGroups(formData.application); }, [formData.application, loadAppGroups]);

  const handleDragStart = (idx: number) => { setDragItem(String(idx)); };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (dragItem === null) return;
    const tmpl = FLOW_TEMPLATES[Number(dragItem)];
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const newNode: FlowNode = {
      id: `node-${Date.now()}`, type: tmpl.type, label: tmpl.label, value: tmpl.prefix,
      x: Math.max(0, Math.min(x - 70, rect.width - 140)),
      y: Math.max(0, Math.min(y - 20, rect.height - 40)),
    };
    setNodes(prev => [...prev, newNode]);
    setDragItem(null);
    if (nodes.length > 0) {
      const last = nodes[nodes.length - 1];
      setConnections(prev => [...prev, { from: last.id, to: newNode.id }]);
    }
  };

  const selectNode = (nodeId: string) => {
    const node = nodes.find(n => n.id === nodeId);
    if (node) { setSelectedNode(nodeId); setEditLabel(node.label); setEditValue(node.value); }
  };

  const updateNode = () => {
    if (!selectedNode) return;
    setNodes(prev => prev.map(n => n.id === selectedNode ? { ...n, label: editLabel, value: editValue } : n));
    setSelectedNode(null);
  };

  const removeNode = (nodeId: string) => {
    setNodes(prev => prev.filter(n => n.id !== nodeId));
    setConnections(prev => prev.filter(c => c.from !== nodeId && c.to !== nodeId));
    if (selectedNode === nodeId) setSelectedNode(null);
  };

  const buildRuleFromWorkflow = () => {
    const srcNode = nodes.find(n => n.type === 'source');
    const dstNode = nodes.find(n => n.type === 'destination');
    const actNode = nodes.find(n => n.type === 'action');
    const zoneNode = nodes.find(n => n.type === 'zone');
    if (srcNode) setFormData(prev => ({ ...prev, source: srcNode.value, source_zone: zoneNode?.value || 'Standard' }));
    if (dstNode) setFormData(prev => ({ ...prev, destination: dstNode.value, destination_zone: zoneNode?.value || 'Standard' }));
    if (actNode) setFormData(prev => ({ ...prev, action: actNode.value === 'allow' ? 'Allow' : 'Deny' }));
    setShowForm(true);
  };

  const handleServicePreset = (preset: typeof SERVICE_PRESETS[0]) => {
    setFormData(prev => ({ ...prev, port: preset.port, protocol: preset.protocol }));
  };

  const submitRule = async () => {
    if (!formData.application || !formData.source || !formData.destination) return;
    setSubmitting(true);
    try {
      await createRule({
        source: formData.source, source_zone: formData.source_zone,
        destination: formData.destination, destination_zone: formData.destination_zone,
        port: `${formData.protocol} ${formData.port}`.trim(), protocol: formData.protocol,
        action: formData.action, application: formData.application, environment: formData.environment,
        datacenter: formData.datacenter, description: formData.description,
        is_group_to_group: formData.source.startsWith('grp-') && formData.destination.startsWith('grp-'),
      });
      onRuleCreated();
      setShowForm(false); setNodes([]); setConnections([]);
    } catch { /* error */ }
    setSubmitting(false);
  };

  const clearCanvas = () => { setNodes([]); setConnections([]); setSelectedNode(null); };

  return (
    <div className="space-y-3">
      {/* Flow component palette */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider mr-1">Components:</span>
          {FLOW_TEMPLATES.map((tmpl, idx) => {
            const c = COLOR_MAP[tmpl.color];
            return (
              <div key={idx} draggable onDragStart={() => handleDragStart(idx)}
                className={`flex items-center gap-1 px-2 py-1 text-xs font-medium border rounded cursor-grab hover:shadow-sm transition-shadow ${c.bg} ${c.border} ${c.text}`}>
                <span className={`w-5 h-5 rounded text-[10px] font-bold flex items-center justify-center ${c.icon}`}>{tmpl.icon}</span>
                <span>{tmpl.label}</span>
              </div>
            );
          })}
        </div>
        <div className="flex items-center gap-2">
          <button onClick={clearCanvas} className="px-2 py-1 text-xs text-gray-600 hover:text-red-600 border border-gray-200 rounded hover:border-red-200">Clear</button>
          <button onClick={buildRuleFromWorkflow} disabled={nodes.length === 0}
            className="px-3 py-1 text-xs font-medium text-white bg-indigo-600 rounded hover:bg-indigo-700 disabled:opacity-40">
            Build Rule
          </button>
        </div>
      </div>

      {/* Canvas */}
      <div onDrop={handleDrop} onDragOver={e => e.preventDefault()}
        className="relative bg-gradient-to-br from-slate-50 to-gray-100 border-2 border-dashed border-gray-300 rounded-lg overflow-hidden" style={{ height: '260px' }}>
        {nodes.length === 0 && (
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <p className="text-sm text-gray-400 font-medium">Drag flow components to build your NGDC firewall rule</p>
            <p className="text-xs text-gray-300 mt-1">Source &rarr; Zone &rarr; Policy &rarr; Destination &rarr; Action</p>
          </div>
        )}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 1 }}>
          {connections.map((conn, idx) => {
            const f = nodes.find(n => n.id === conn.from);
            const t = nodes.find(n => n.id === conn.to);
            if (!f || !t) return null;
            const x1 = f.x + 70, y1 = f.y + 18, x2 = t.x + 70, y2 = t.y + 18;
            const mx = (x1 + x2) / 2;
            const strokeColor = t.type === 'action' ? (t.value === 'allow' ? '#22c55e' : '#ef4444') : '#94a3b8';
            return (
              <g key={idx}>
                <path d={`M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`} stroke={strokeColor} strokeWidth="2" fill="none" strokeDasharray="6,3" />
                <polygon points={`${x2-6},${y2-4} ${x2},${y2} ${x2-6},${y2+4}`} fill={strokeColor} />
              </g>
            );
          })}
        </svg>
        {nodes.map(node => {
          const tmpl = FLOW_TEMPLATES.find(t => t.type === node.type) || FLOW_TEMPLATES[0];
          const c = COLOR_MAP[tmpl.color];
          return (
            <div key={node.id} onClick={() => selectNode(node.id)}
              className={`absolute flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium border rounded-lg shadow-sm cursor-pointer transition-all hover:shadow-md ${c.bg} ${c.border} ${c.text} ${selectedNode === node.id ? 'ring-2 ring-indigo-400 ring-offset-1' : ''}`}
              style={{ left: node.x, top: node.y, zIndex: 2, minWidth: '120px' }}>
              <span className={`w-5 h-5 rounded text-[10px] font-bold flex items-center justify-center flex-shrink-0 ${c.icon}`}>
                {node.type === 'source' ? (node.value.startsWith('grp-') ? 'GRP' : node.value.startsWith('svr-') ? 'SVR' : node.value.startsWith('rng-') ? 'RNG' : 'NET') :
                 node.type === 'zone' ? 'SZ' : node.type === 'policy' ? 'POL' : node.type === 'destination' ? (node.value.startsWith('grp-') ? 'GRP' : 'SVR') :
                 node.value === 'allow' ? 'OK' : 'X'}
              </span>
              <span className="truncate max-w-[100px]">{node.label}</span>
              <button onClick={(e) => { e.stopPropagation(); removeNode(node.id); }}
                className="ml-auto text-gray-400 hover:text-red-500 text-xs leading-none flex-shrink-0">&times;</button>
            </div>
          );
        })}
      </div>

      {/* Node editor */}
      {selectedNode && (
        <div className="flex items-center gap-2 p-2 bg-white border border-gray-200 rounded-lg">
          <span className="text-xs text-gray-500 font-medium">Edit:</span>
          <input className="flex-1 px-2 py-1 text-xs border border-gray-200 rounded" value={editLabel} onChange={e => setEditLabel(e.target.value)} placeholder="Label" />
          <input className="flex-1 px-2 py-1 text-xs border border-gray-200 rounded font-mono" value={editValue} onChange={e => setEditValue(e.target.value)} placeholder="e.g. grp-CRM-NH01-STD-WEB" />
          {appGroups.length > 0 && (
            <select className="px-2 py-1 text-xs border rounded" value="" onChange={e => { if (e.target.value) setEditValue(e.target.value); }}>
              <option value="">Pick group...</option>
              {appGroups.map(g => <option key={g.name} value={g.name}>{g.name} ({g.members.length})</option>)}
            </select>
          )}
          <button onClick={updateNode} className="px-2 py-1 text-xs font-medium text-white bg-blue-600 rounded hover:bg-blue-700">Save</button>
          <button onClick={() => setSelectedNode(null)} className="px-2 py-1 text-xs text-gray-600 hover:text-gray-800">Cancel</button>
        </div>
      )}

      {/* Rule form */}
      {showForm && (
        <div className="p-4 bg-white border border-indigo-200 rounded-lg shadow-sm">
          <h4 className="text-sm font-semibold text-indigo-800 mb-3">Configure NGDC Firewall Rule</h4>
          <div className="grid grid-cols-4 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Application</label>
              <select className="w-full px-2 py-1.5 text-xs border rounded" value={formData.application} onChange={e => setFormData({...formData, application: e.target.value})}>
                <option value="">Select...</option>
                {applications.map(a => <option key={a.app_id} value={a.app_id}>{a.app_id} - {a.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Environment</label>
              <select className="w-full px-2 py-1.5 text-xs border rounded" value={formData.environment} onChange={e => setFormData({...formData, environment: e.target.value})}>
                <option>Production</option><option>Non-Production</option><option>Pre-Production</option>
                <option>Development</option><option>UAT</option><option>DR</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Neighbourhood</label>
              <select className="w-full px-2 py-1.5 text-xs border rounded" value={formData.nh} onChange={e => setFormData({...formData, nh: e.target.value})}>
                <option value="">Select NH...</option>
                {neighbourhoods.map(nh => <option key={nh.nh_id} value={nh.nh_id}>{nh.nh_id} - {nh.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Security Zone</label>
              <select className="w-full px-2 py-1.5 text-xs border rounded" value={formData.sz} onChange={e => setFormData({...formData, sz: e.target.value, source_zone: e.target.value, destination_zone: e.target.value})}>
                <option value="">Select SZ...</option>
                {securityZones.map(sz => <option key={sz.code} value={sz.code}>{sz.code} - {sz.name}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-4 gap-3 mt-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Source (NGDC Name)</label>
              <input className="w-full px-2 py-1.5 text-xs border rounded font-mono" value={formData.source} onChange={e => setFormData({...formData, source: e.target.value})} placeholder="grp-APP-NH01-STD-WEB" />
              {formData.source && !formData.source.startsWith('grp-') && !formData.source.startsWith('svr-') && !formData.source.startsWith('rng-') && formData.source.length > 0 && (
                <p className="text-[10px] text-amber-600 mt-0.5">Use svr- for IPs, rng- for ranges, grp- for groups</p>
              )}
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Destination (NGDC Name)</label>
              <input className="w-full px-2 py-1.5 text-xs border rounded font-mono" value={formData.destination} onChange={e => setFormData({...formData, destination: e.target.value})} placeholder="grp-APP-NH01-STD-DB" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Service Preset</label>
              <select className="w-full px-2 py-1.5 text-xs border rounded" value="" onChange={e => {
                const p = SERVICE_PRESETS.find(s => s.label === e.target.value);
                if (p) handleServicePreset(p);
              }}>
                <option value="">Select preset...</option>
                {SERVICE_PRESETS.map(s => <option key={s.label} value={s.label}>{s.label}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Port / Protocol</label>
              <div className="flex gap-1">
                <input className="w-1/2 px-2 py-1.5 text-xs border rounded" value={formData.port} onChange={e => setFormData({...formData, port: e.target.value})} />
                <select className="w-1/2 px-1 py-1.5 text-xs border rounded" value={formData.protocol} onChange={e => setFormData({...formData, protocol: e.target.value})}>
                  <option>TCP</option><option>UDP</option><option>ICMP</option><option>Any</option>
                </select>
              </div>
            </div>
          </div>
          <div className="mt-3">
            <label className="block text-xs font-medium text-gray-600 mb-1">Description</label>
            <input className="w-full px-2 py-1.5 text-xs border rounded" value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} placeholder="Rule description..." />
          </div>
          <div className="flex justify-end gap-2 mt-3">
            <button onClick={() => setShowForm(false)} className="px-3 py-1.5 text-xs text-gray-600 border rounded hover:bg-gray-50">Cancel</button>
            <button onClick={submitRule} disabled={!formData.application || !formData.source || !formData.destination || submitting}
              className="px-4 py-1.5 text-xs font-medium text-white bg-indigo-600 rounded hover:bg-indigo-700 disabled:opacity-40">
              {submitting ? 'Creating...' : 'Create NGDC Rule'}
            </button>
          </div>
        </div>
      )}

      <div className="text-xs text-gray-500">
        Drag components to canvas: Source &rarr; Zone &rarr; Policy &rarr; Destination &rarr; Action. Uses NGDC naming (svr-, rng-, grp-).
      </div>
    </div>
  );
}
