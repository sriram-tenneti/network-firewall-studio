import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import HomePage from '@/pages/HomePage';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

describe('HomePage', () => {
  it('renders the main title', () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    expect(screen.getByText('Network Firewall Studio')).toBeInTheDocument();
  });

  it('renders all three module cards', () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    expect(screen.getByText('Firewall Studio')).toBeInTheDocument();
    expect(screen.getByText('NGDC Standardization')).toBeInTheDocument();
    expect(screen.getByText('Network Firewall Request')).toBeInTheDocument();
  });

  it('renders module subtitles', () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    expect(screen.getByText('Design & Manage NGDC Rules')).toBeInTheDocument();
    expect(screen.getByText('Migrate Legacy to NGDC')).toBeInTheDocument();
    expect(screen.getByText('Manage As-Is Firewall Rules')).toBeInTheDocument();
  });

  it('renders feature lists', () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    expect(screen.getByText('Rule Design & Builder')).toBeInTheDocument();
    expect(screen.getByText('Legacy Rule Import')).toBeInTheDocument();
    expect(screen.getByText('View Existing Rules')).toBeInTheDocument();
  });

  it('renders quick stats', () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    expect(screen.getByText('NGDC Data Centers')).toBeInTheDocument();
    expect(screen.getByText('Neighbourhoods')).toBeInTheDocument();
    expect(screen.getByText('Security Zones')).toBeInTheDocument();
    expect(screen.getByText('Policy Matrices')).toBeInTheDocument();
  });

  it('renders footer links', () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    expect(screen.getByText('Settings & Org Admin')).toBeInTheDocument();
    expect(screen.getByText('Enterprise Firewall Management Platform')).toBeInTheDocument();
  });

  it('renders Open Module CTAs', () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    const ctas = screen.getAllByText('Open Module');
    expect(ctas).toHaveLength(3);
  });

  it('navigates to firewall-studio on card click', async () => {
    const { container } = render(<MemoryRouter><HomePage /></MemoryRouter>);
    const buttons = container.querySelectorAll('button');
    const fwButton = Array.from(buttons).find(b => b.textContent?.includes('Firewall Studio'));
    fwButton?.click();
    expect(mockNavigate).toHaveBeenCalledWith('/firewall-studio');
  });

  it('navigates to ngdc-standardization on card click', () => {
    const { container } = render(<MemoryRouter><HomePage /></MemoryRouter>);
    const buttons = container.querySelectorAll('button');
    const ngdcButton = Array.from(buttons).find(b => b.textContent?.includes('NGDC Standardization'));
    ngdcButton?.click();
    expect(mockNavigate).toHaveBeenCalledWith('/ngdc-standardization');
  });

  it('navigates to settings on footer click', () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    screen.getByText('Settings & Org Admin').click();
    expect(mockNavigate).toHaveBeenCalledWith('/settings');
  });
});
