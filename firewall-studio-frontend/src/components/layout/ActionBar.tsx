import { Plus, Edit, Trash2, Shield, RefreshCw, History, Users, ChevronDown } from 'lucide-react';

interface ActionBarProps {
  mode: 'design' | 'migration';
  onAdd?: () => void;
  onModify?: () => void;
  onDelete?: () => void;
  onCertify?: () => void;
  onReCertify?: () => void;
  onViewHistory?: () => void;
}

export function ActionBar({ mode, onAdd, onModify, onDelete, onCertify, onReCertify, onViewHistory }: ActionBarProps) {
  const buttons = mode === 'design'
    ? [
        { label: 'All', icon: Plus, onClick: onAdd, primary: true },
        { label: 'Modify', icon: Edit, onClick: onModify },
        { label: 'Delete', icon: Trash2, onClick: onDelete },
        { label: 'Certify', icon: Shield, onClick: onCertify },
        { label: 'Re Certify', icon: RefreshCw, onClick: onReCertify },
        { label: 'View History', icon: History, onClick: onViewHistory },
      ]
    : [
        { label: 'Add', icon: Plus, onClick: onAdd, primary: true },
        { label: 'Modify', icon: Edit, onClick: onModify },
        { label: 'Delete', icon: Trash2, onClick: onDelete },
        { label: 'Certify', icon: Shield, onClick: onCertify },
        { label: 'View History', icon: History, onClick: onViewHistory },
      ];

  return (
    <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-6 py-2">
      <div className="flex items-center gap-1">
        {buttons.map((btn) => (
          <button
            key={btn.label}
            onClick={btn.onClick}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              btn.primary
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'text-slate-600 hover:bg-slate-200'
            }`}
          >
            <btn.icon className="h-3.5 w-3.5" />
            {btn.label}
          </button>
        ))}
      </div>
      <div className="flex items-center gap-2">
        <button className="flex items-center gap-1 rounded-md p-1.5 text-slate-500 hover:bg-slate-200">
          <Users className="h-4 w-4" />
        </button>
        <div className="flex items-center gap-1 text-sm text-slate-600">
          <span>Jon</span>
          <ChevronDown className="h-3 w-3" />
        </div>
      </div>
    </div>
  );
}
