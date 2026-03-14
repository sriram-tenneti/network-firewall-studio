import { useState, useEffect } from 'react';
import { Modal } from '../shared/Modal';
import type { FirewallRule, Application } from '@/types';

interface RuleFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: Record<string, string | boolean>) => void;
  rule?: FirewallRule | null;
  applications: Application[];
  mode: 'create' | 'edit';
}

export function RuleFormModal({ isOpen, onClose, onSave, rule, applications, mode }: RuleFormModalProps) {
  const [form, setForm] = useState({
    application: '',
    source: '',
    source_zone: '',
    destination: '',
    destination_zone: '',
    port: '',
    protocol: 'TCP',
    action: 'Allow',
    description: '',
    environment: 'Production',
    datacenter: 'ALPHA_NGDC',
    is_group_to_group: true,
  });

  useEffect(() => {
    if (rule && mode === 'edit') {
      setForm({
        application: rule.application || '',
        source: typeof rule.source === 'string' ? rule.source : (rule.source as unknown as Record<string, string>)?.group_name || '',
        source_zone: typeof rule.source === 'object' ? (rule.source as unknown as Record<string, string>)?.security_zone || '' : '',
        destination: typeof rule.destination === 'string' ? rule.destination : (rule.destination as unknown as Record<string, string>)?.name || '',
        destination_zone: typeof rule.destination === 'object' ? (rule.destination as unknown as Record<string, string>)?.security_zone || '' : '',
        port: typeof rule.source === 'object' ? (rule.source as unknown as Record<string, string>)?.ports || '' : '',
        protocol: 'TCP',
        action: 'Allow',
        description: '',
        environment: rule.environment || 'Production',
        datacenter: rule.datacenter || 'ALPHA_NGDC',
        is_group_to_group: true,
      });
    } else if (mode === 'create') {
      setForm({
        application: '',
        source: '',
        source_zone: '',
        destination: '',
        destination_zone: '',
        port: '',
        protocol: 'TCP',
        action: 'Allow',
        description: '',
        environment: 'Production',
        datacenter: 'ALPHA_NGDC',
        is_group_to_group: true,
      });
    }
  }, [rule, mode, isOpen]);

  const handleSubmit = () => {
    onSave(form);
    onClose();
  };

  const inputClass = 'w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white';
  const labelClass = 'block text-sm font-medium text-gray-700 mb-1';

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={mode === 'create' ? 'Create New Firewall Rule' : 'Edit Firewall Rule'} size="lg">
      <div className="space-y-4 p-1">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Application</label>
            <select className={inputClass} value={form.application} onChange={e => setForm({ ...form, application: e.target.value })}>
              <option value="">Select Application</option>
              {applications.map(app => (
                <option key={app.app_id} value={app.app_id}>{app.app_id} - {app.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className={labelClass}>Environment</label>
            <select className={inputClass} value={form.environment} onChange={e => setForm({ ...form, environment: e.target.value })}>
              <option value="Production">Production</option>
              <option value="Non-Production">Non-Production</option>
              <option value="Pre-Production">Pre-Production</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Source (Group/IP)</label>
            <input className={inputClass} placeholder="e.g. grp-APP01-NH01-STD-src" value={form.source} onChange={e => setForm({ ...form, source: e.target.value })} />
          </div>
          <div>
            <label className={labelClass}>Source Zone</label>
            <select className={inputClass} value={form.source_zone} onChange={e => setForm({ ...form, source_zone: e.target.value })}>
              <option value="">Select Zone</option>
              <option value="Standard">Standard</option>
              <option value="CCS">CCS</option>
              <option value="CDE">CDE</option>
              <option value="CPA">CPA</option>
              <option value="PSE">PSE</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Destination (Group/IP)</label>
            <input className={inputClass} placeholder="e.g. grp-APP01-NH01-STD-dst" value={form.destination} onChange={e => setForm({ ...form, destination: e.target.value })} />
          </div>
          <div>
            <label className={labelClass}>Destination Zone</label>
            <select className={inputClass} value={form.destination_zone} onChange={e => setForm({ ...form, destination_zone: e.target.value })}>
              <option value="">Select Zone</option>
              <option value="Standard">Standard</option>
              <option value="CCS">CCS</option>
              <option value="CDE">CDE</option>
              <option value="CPA">CPA</option>
              <option value="PSE">PSE</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className={labelClass}>Port</label>
            <input className={inputClass} placeholder="e.g. 443, 8080-8090" value={form.port} onChange={e => setForm({ ...form, port: e.target.value })} />
          </div>
          <div>
            <label className={labelClass}>Protocol</label>
            <select className={inputClass} value={form.protocol} onChange={e => setForm({ ...form, protocol: e.target.value })}>
              <option value="TCP">TCP</option>
              <option value="UDP">UDP</option>
              <option value="ICMP">ICMP</option>
              <option value="ANY">ANY</option>
            </select>
          </div>
          <div>
            <label className={labelClass}>Action</label>
            <select className={inputClass} value={form.action} onChange={e => setForm({ ...form, action: e.target.value })}>
              <option value="Allow">Allow</option>
              <option value="Deny">Deny</option>
            </select>
          </div>
        </div>

        <div>
          <label className={labelClass}>Description</label>
          <textarea className={inputClass + ' h-20 resize-none'} placeholder="Rule description..." value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Datacenter</label>
            <select className={inputClass} value={form.datacenter} onChange={e => setForm({ ...form, datacenter: e.target.value })}>
              <option value="ALPHA_NGDC">Alpha NGDC</option>
              <option value="BETA_NGDC">Beta NGDC</option>
              <option value="GAMMA_NGDC">Gamma NGDC</option>
            </select>
          </div>
          <div className="flex items-end">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" className="w-4 h-4 text-blue-600 rounded" checked={form.is_group_to_group} onChange={e => setForm({ ...form, is_group_to_group: e.target.checked })} />
              <span className="text-sm text-gray-700">Group-to-Group Rule</span>
            </label>
          </div>
        </div>
      </div>

      <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
        <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
        <button onClick={handleSubmit} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700">{mode === 'create' ? 'Create Rule' : 'Update Rule'}</button>
      </div>
    </Modal>
  );
}
