import { useState } from 'react';
import { Header } from '@/components/layout/Header';
import { DesignStudioPage } from '@/pages/DesignStudioPage';
import { MigrationStudioPage } from '@/pages/MigrationStudioPage';

function App() {
  const [currentPage, setCurrentPage] = useState<'design' | 'migration'>('design');

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
        {currentPage === 'design' ? <DesignStudioPage /> : <MigrationStudioPage />}
      </main>
    </div>
  );
}

export default App
