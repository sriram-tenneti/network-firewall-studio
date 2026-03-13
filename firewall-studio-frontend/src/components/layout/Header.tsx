import { Shield, Menu, Plus, ChevronDown, User } from 'lucide-react';

interface HeaderProps {
  currentPage: 'design' | 'migration' | 'admin';
  onNavigate: (page: 'design' | 'migration' | 'admin') => void;
  application?: string;
  environment?: string;
  datacenter?: string;
}

export function Header({ currentPage, onNavigate, application, environment, datacenter }: HeaderProps) {
  return (
    <header className="bg-gradient-to-r from-slate-800 to-slate-700 text-white shadow-lg">
      <div className="flex items-center justify-between px-6 py-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Shield className="h-7 w-7 text-blue-400" />
            <h1 className="text-lg font-bold tracking-tight">
              {currentPage === 'design' ? 'Network Firewall Design Studio' : 'Network Firewall Migration Studio'}
            </h1>
          </div>

          {application && (
            <div className="ml-6 flex items-center gap-4 text-sm text-slate-300">
              <span>Application: <strong className="text-white">{application}</strong></span>
              {environment && (
                <span>Environment: <strong className="text-amber-300">{environment}</strong></span>
              )}
              {datacenter && (
                <span>Datacenter: <strong className="text-white">{datacenter}</strong></span>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('design')}
            className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              currentPage === 'design'
                ? 'bg-blue-600 text-white'
                : 'text-slate-300 hover:bg-slate-600 hover:text-white'
            }`}
          >
            Design Studio
          </button>
          <button
            onClick={() => onNavigate('migration')}
            className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              currentPage === 'migration'
                ? 'bg-blue-600 text-white'
                : 'text-slate-300 hover:bg-slate-600 hover:text-white'
            }`}
          >
            Migration Studio
          </button>
          <button
            onClick={() => onNavigate('admin')}
            className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              currentPage === 'admin'
                ? 'bg-blue-600 text-white'
                : 'text-slate-300 hover:bg-slate-600 hover:text-white'
            }`}
          >
            Org Admin
          </button>

          <div className="ml-4 flex items-center gap-2">
            <button className="flex items-center gap-1 rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium hover:bg-blue-500 transition-colors">
              <Plus className="h-4 w-4" />
              Add
              <ChevronDown className="h-3 w-3" />
            </button>
          </div>

          <button className="rounded-md p-1.5 hover:bg-slate-600 transition-colors">
            <Menu className="h-5 w-5" />
          </button>

          <div className="flex items-center gap-2 ml-2 rounded-full bg-slate-600 px-3 py-1">
            <User className="h-4 w-4" />
            <span className="text-sm font-medium">Jon</span>
            <ChevronDown className="h-3 w-3" />
          </div>
        </div>
      </div>
    </header>
  );
}
