import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Header } from '@/components/layout/Header';
import { DesignStudioPage } from '@/pages/DesignStudioPage';
import { MigrationStudioPage } from '@/pages/MigrationStudioPage';
import ReviewPage from '@/pages/ReviewPage';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main>
          <Routes>
            <Route path="/" element={<DesignStudioPage />} />
            <Route path="/migration" element={<MigrationStudioPage />} />
            <Route path="/review" element={<ReviewPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
