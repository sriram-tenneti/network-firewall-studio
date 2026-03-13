import { useState } from 'react';
import { Header } from '@/components/layout/Header';
import { DesignStudioPage } from '@/pages/DesignStudioPage';
import { MigrationStudioPage } from '@/pages/MigrationStudioPage';
import { OrgAdminPage } from '@/pages/OrgAdminPage';

function App() {
  const [currentPage, setCurrentPage] = useState<'design' | 'migration' | 'admin'>('design');

  const renderPage = () => {
    switch (currentPage) {
      case 'design': return <DesignStudioPage />;
      case 'migration': return <MigrationStudioPage />;
      case 'admin': return <OrgAdminPage />;
    }
  };

  return (
    <div className="flex h-screen flex-col bg-slate-100">
      <Header
        currentPage={currentPage}
        onNavigate={setCurrentPage}
        application={currentPage === 'design' ? 'Ordering System' : undefined}
        environment={currentPage === 'design' ? 'Production' : undefined}
        datacenter={currentPage === 'design' ? 'DC1' : undefined}
      />
      <main className="flex-1 overflow-hidden">
        {renderPage()}
      </main>
    </div>
  );
}

export default App
