import { useState } from 'react';
import type { Application } from '@/types';

interface DragDropRuleBuilderProps {
  applications: Application[];
  onRuleCreated: () => void;
}

interface WorkflowNode {
  id: string;
  type: 'source' | 'policy' | 'destination' | 'action';
  label: string;
  value: string;
  x: number;
  y: number;
}

interface WorkflowConnection {
  from: string;
  to: string;
}

const TEMPLATES = [
  { label: 'Source (Group)', type: 'source' as const, icon: 'GRP', value: 'grp-' },
  { label: 'Source (IP)', type: 'source' as const, icon: 'IP', value: 'ip-' },
  { label: 'Source (Subnet)', type: 'source' as const, icon: 'NET', value: 'subnet-' },
  { label: 'Policy Check', type: 'policy' as const, icon: 'POL', value: 'policy' },
  { label: 'Destination', type: 'destination' as const, icon: 'DST', value: 'dest-' },
  { label: 'Allow', type: 'action' as const, icon: 'OK', value: 'allow' },
  { label: 'Deny', type: 'action' as const, icon: 'X', value: 'deny' },
];

const NODE_COLORS: Record<string, string> = {
  source: 'bg-blue-50 border-blue-300 text-blue-800',
  policy: 'bg-amber-50 border-amber-300 text-amber-800',
  destination: 'bg-emerald-50 border-emerald-300 text-emerald-800',
  action: 'bg-purple-50 border-purple-300 text-purple-800',
};

const ICON_COLORS: Record<string, string> = {
  source: 'bg-blue-200 text-blue-700',
  policy: 'bg-amber-200 text-amber-700',
  destination: 'bg-emerald-200 text-emerald-700',
  action: 'bg-purple-200 text-purple-700',
};

export function DragDropRuleBuilder({ applications, onRuleCreated }: DragDropRuleBuilderProps) {
  const [nodes, setNodes] = useState<WorkflowNode[]>([]);
  const [connections, setConnections] = useState<WorkflowConnection[]>([]);
  const [dragItem, setDragItem] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [editLabel, setEditLabel] = useState('');
  const [editValue, setEditValue] = useState('');
  const [showForm, setShowForm] = useState(false);

  const [formData, setFormData] = useState({
    application: '',
    environment: 'Production',
    source: '',
    source_zone: '',
    destination: '',
    destination_zone: '',
    port: '443',
    protocol: 'TCP',
    action: 'Allow',
  });

  const handleDragStart = (templateIdx: number) => {
    setDragItem(String(templateIdx));
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (dragItem === null) return;
    const tmpl = TEMPLATES[Number(dragItem)];
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const newNode: WorkflowNode = {
      id: `node-${Date.now()}`,
      type: tmpl.type,
      label: tmpl.label,
      value: tmpl.value,
      x: Math.max(0, Math.min(x - 60, rect.width - 120)),
      y: Math.max(0, Math.min(y - 16, rect.height - 32)),
    };
    setNodes(prev => [...prev, newNode]);
    setDragItem(null);

    if (nodes.length > 0) {
      const lastNode = nodes[nodes.length - 1];
      setConnections(prev => [...prev, { from: lastNode.id, to: newNode.id }]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const selectNode = (nodeId: string) => {
    const node = nodes.find(n => n.id === nodeId);
    if (node) {
      setSelectedNode(nodeId);
      setEditLabel(node.label);
      setEditValue(node.value);
    }
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
    const sourceNode = nodes.find(n => n.type === 'source');
    const destNode = nodes.find(n => n.type === 'destination');
    const actionNode = nodes.find(n => n.type === 'action');
    if (sourceNode) {
      setFormData(prev => ({ ...prev, source: sourceNode.value, source_zone: 'Standard' }));
    }
    if (destNode) {
      setFormData(prev => ({ ...prev, destination: destNode.value, destination_zone: 'Standard' }));
    }
    if (actionNode) {
      setFormData(prev => ({ ...prev, action: actionNode.value === 'allow' ? 'Allow' : 'Deny' }));
    }
    setShowForm(true);
  };

  const submitRule = () => {
    onRuleCreated();
    setShowForm(false);
    setNodes([]);
    setConnections([]);
  };

  const clearCanvas = () => {
    setNodes([]);
    setConnections([]);
    setSelectedNode(null);
  };

  return (
    <div className="space-y-3">
      {/* Compact toolbar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider mr-2">Drag to canvas:</span>
          {TEMPLATES.map((tmpl, idx) => (
            <div
              key={idx}
              draggable
              onDragStart={() => handleDragStart(idx)}
              className={`flex items-center gap-1 px-2 py-1 text-xs font-medium border rounded cursor-grab hover:shadow-sm transition-shadow ${NODE_COLORS[tmpl.type]}`}
            >
              <span className={`w-5 h-5 rounded text-[10px] font-bold flex items-center justify-center ${ICON_COLORS[tmpl.type]}`}>{tmpl.icon}</span>
              <span>{tmpl.label}</span>
            </div>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <button onClick={clearCanvas} className="px-2 py-1 text-xs text-gray-600 hover:text-red-600 border border-gray-200 rounded hover:border-red-200">Clear</button>
          <button
            onClick={buildRuleFromWorkflow}
            disabled={nodes.length === 0}
            className="px-3 py-1 text-xs font-medium text-white bg-indigo-600 rounded hover:bg-indigo-700 disabled:opacity-40"
          >
            Build Rule
          </button>
        </div>
      </div>

      {/* Canvas area - compact */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        className="relative bg-gradient-to-br from-slate-50 to-gray-100 border-2 border-dashed border-gray-300 rounded-lg overflow-hidden"
        style={{ height: '220px' }}
      >
        {nodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-sm text-gray-400">Drag components here to build your firewall rule workflow</p>
          </div>
        )}

        {/* SVG connections */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 1 }}>
          {connections.map((conn, idx) => {
            const fromNode = nodes.find(n => n.id === conn.from);
            const toNode = nodes.find(n => n.id === conn.to);
            if (!fromNode || !toNode) return null;
            const x1 = fromNode.x + 60;
            const y1 = fromNode.y + 16;
            const x2 = toNode.x + 60;
            const y2 = toNode.y + 16;
            const midX = (x1 + x2) / 2;
            return (
              <g key={idx}>
                <path
                  d={`M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`}
                  stroke="#94a3b8"
                  strokeWidth="1.5"
                  fill="none"
                  strokeDasharray="4,3"
                />
                <circle cx={x2} cy={y2} r="3" fill="#94a3b8" />
              </g>
            );
          })}
        </svg>

        {/* Nodes */}
        {nodes.map(node => (
          <div
            key={node.id}
            onClick={() => selectNode(node.id)}
            className={`absolute flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium border rounded-md shadow-sm cursor-pointer transition-all hover:shadow-md ${NODE_COLORS[node.type]} ${selectedNode === node.id ? 'ring-2 ring-indigo-400' : ''}`}
            style={{ left: node.x, top: node.y, zIndex: 2, minWidth: '100px' }}
          >
            <span className="truncate">{node.label}</span>
            <button
              onClick={(e) => { e.stopPropagation(); removeNode(node.id); }}
              className="ml-auto text-gray-400 hover:text-red-500 text-xs leading-none"
            >&times;</button>
          </div>
        ))}
      </div>

      {/* Inline node editor */}
      {selectedNode && (
        <div className="flex items-center gap-2 p-2 bg-white border border-gray-200 rounded-lg">
          <span className="text-xs text-gray-500 font-medium">Edit:</span>
          <input
            className="flex-1 px-2 py-1 text-xs border border-gray-200 rounded"
            value={editLabel}
            onChange={e => setEditLabel(e.target.value)}
            placeholder="Label"
          />
          <input
            className="flex-1 px-2 py-1 text-xs border border-gray-200 rounded"
            value={editValue}
            onChange={e => setEditValue(e.target.value)}
            placeholder="Value (e.g. grp-APP01-NH01-STD-web)"
          />
          <button onClick={updateNode} className="px-2 py-1 text-xs font-medium text-white bg-blue-600 rounded hover:bg-blue-700">Save</button>
          <button onClick={() => setSelectedNode(null)} className="px-2 py-1 text-xs text-gray-600 hover:text-gray-800">Cancel</button>
        </div>
      )}

      {/* Rule form from workflow */}
      {showForm && (
        <div className="p-4 bg-white border border-indigo-200 rounded-lg shadow-sm">
          <h4 className="text-sm font-semibold text-indigo-800 mb-3">Configure Rule from Workflow</h4>
          <div className="grid grid-cols-4 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Application</label>
              <select className="w-full px-2 py-1.5 text-xs border rounded" value={formData.application} onChange={e => setFormData({...formData, application: e.target.value})}>
                <option value="">Select...</option>
                {applications.map(a => <option key={a.app_id} value={a.app_id}>{a.app_id} - {a.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Source</label>
              <input className="w-full px-2 py-1.5 text-xs border rounded" value={formData.source} onChange={e => setFormData({...formData, source: e.target.value})} />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Destination</label>
              <input className="w-full px-2 py-1.5 text-xs border rounded" value={formData.destination} onChange={e => setFormData({...formData, destination: e.target.value})} />
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
          <div className="flex justify-end gap-2 mt-3">
            <button onClick={() => setShowForm(false)} className="px-3 py-1.5 text-xs text-gray-600 border rounded hover:bg-gray-50">Cancel</button>
            <button onClick={submitRule} disabled={!formData.application} className="px-4 py-1.5 text-xs font-medium text-white bg-indigo-600 rounded hover:bg-indigo-700 disabled:opacity-40">Create Rule</button>
          </div>
        </div>
      )}

      {/* Hint */}
      <div className="text-xs text-gray-500">
        Drag components to the canvas, connect them, then click &quot;Build Rule&quot; to configure.
      </div>
    </div>
  );
}
