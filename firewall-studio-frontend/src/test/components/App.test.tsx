import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '@/App';

// Mock all page components to avoid heavy renders
vi.mock('@/pages/HomePage', () => ({ default: () => <div data-testid="home-page">HomePage</div> }));
vi.mock('@/pages/DesignStudioPage', () => ({ DesignStudioPage: () => <div>DesignStudio</div> }));
vi.mock('@/pages/MigrationStudioPage', () => ({ MigrationStudioPage: () => <div>MigrationStudio</div> }));
vi.mock('@/pages/ReviewPage', () => ({ default: () => <div>ReviewPage</div> }));
vi.mock('@/pages/FirewallManagementPage', () => ({ default: () => <div>FirewallManagement</div> }));
vi.mock('@/pages/DataImportPage', () => ({ default: () => <div>DataImport</div> }));
vi.mock('@/pages/SettingsPage', () => ({ default: () => <div>SettingsPage</div> }));
vi.mock('@/pages/AdminPage', () => ({ default: () => <div>AdminPage</div> }));
vi.mock('@/pages/LifecycleDashboardPage', () => ({ default: () => <div>LifecycleDashboard</div> }));
vi.mock('@/components/layout/ModuleLayout', () => ({
  ModuleLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />);
    expect(screen.getByTestId('home-page')).toBeInTheDocument();
  });

  it('renders HomePage at root route', () => {
    render(<App />);
    expect(screen.getByText('HomePage')).toBeInTheDocument();
  });
});
