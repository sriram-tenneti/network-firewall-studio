import { Link, useLocation } from 'react-router-dom';

const navItems = [
  { path: '/', label: 'Design Studio' },
  { path: '/migration', label: 'Migration Studio' },
  { path: '/review', label: 'Review & Approval' },
];

export function Header() {
  const location = useLocation();

  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-[1600px] mx-auto px-6">
        <div className="flex items-center justify-between h-14">
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
                <span className="text-white font-bold text-sm">NF</span>
              </div>
              <span className="text-lg font-bold text-gray-900">Network Firewall Studio</span>
            </Link>
            <nav className="flex items-center gap-1">
              {navItems.map(item => {
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={'px-3 py-2 rounded-md text-sm font-medium transition-colors ' + (
                      isActive
                        ? 'bg-blue-50 text-blue-700'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    )}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-500">Enterprise Firewall Management</span>
          </div>
        </div>
      </div>
    </header>
  );
}
