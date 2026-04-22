import { useEffect, useMemo, useRef, useState } from 'react';
import type { PortCatalogEntry } from '@/lib/api';
import * as api from '@/lib/api';

interface PortPickerProps {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  className?: string;
}

/** Parse the freeform "ports" field into a list of tokens like "TCP 443". */
function parsePorts(v: string): string[] {
  return v.split(',').map((t) => t.trim()).filter(Boolean);
}

function portToken(p: PortCatalogEntry): string {
  if (p.protocol === 'ICMP') return 'ICMP';
  return `${(p.protocol || 'TCP').toUpperCase()} ${p.port}`;
}

function humanLabel(p: PortCatalogEntry): string {
  if (p.protocol === 'ICMP') return `${p.name} (ICMP)`;
  return `${p.name} · ${p.protocol || 'TCP'} ${p.port}`;
}

export default function PortPicker({ value, onChange, placeholder = 'Pick a port…', className = '' }: PortPickerProps) {
  const [catalog, setCatalog] = useState<PortCatalogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState<string>('All');
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const list = await api.listPorts();
        if (!cancelled) setCatalog(list || []);
      } catch {
        if (!cancelled) setCatalog([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    const onClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, []);

  const categories = useMemo(() => {
    const s = new Set<string>(['All']);
    for (const p of catalog) if (p.category) s.add(p.category);
    return Array.from(s);
  }, [catalog]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return catalog.filter((p) => {
      if (category !== 'All' && p.category !== category) return false;
      if (!q) return true;
      return (
        p.name.toLowerCase().includes(q) ||
        p.port_id.toLowerCase().includes(q) ||
        String(p.port).includes(q) ||
        (p.description || '').toLowerCase().includes(q) ||
        (p.aliases || []).some((a) => a.toLowerCase().includes(q))
      );
    });
  }, [catalog, query, category]);

  const tokens = parsePorts(value);

  const addToken = (t: string) => {
    const cur = parsePorts(value);
    if (cur.includes(t)) { setOpen(false); return; }
    const next = [...cur, t].join(', ');
    onChange(next);
    setOpen(false);
    setQuery('');
  };

  const removeToken = (t: string) => {
    const next = parsePorts(value).filter((x) => x !== t).join(', ');
    onChange(next);
  };

  return (
    <div ref={ref} className={`relative ${className}`}>
      <div className="flex flex-wrap items-center gap-1 min-h-[38px] border border-gray-300 rounded-lg px-2 py-1.5 bg-white focus-within:ring-2 focus-within:ring-indigo-300">
        {tokens.length === 0 && !open && (
          <span className="text-xs text-gray-400 px-1">{placeholder}</span>
        )}
        {tokens.map((t) => (
          <span key={t} className="inline-flex items-center gap-1 text-[11px] font-mono font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200 rounded px-1.5 py-0.5">
            {t}
            <button type="button" onClick={() => removeToken(t)} className="text-indigo-400 hover:text-indigo-700" aria-label="remove">×</button>
          </span>
        ))}
        <input
          value={query}
          onFocus={() => setOpen(true)}
          onChange={(e) => { setQuery(e.target.value); setOpen(true); }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && query.trim()) {
              // Allow freeform entry like "TCP 9999" or just "9999"
              const raw = query.trim().toUpperCase();
              const withProto = /^(TCP|UDP|ICMP)\s+/.test(raw) ? raw : `TCP ${raw}`;
              addToken(withProto);
              e.preventDefault();
            }
          }}
          placeholder={tokens.length === 0 ? '' : '+ add'}
          className="flex-1 min-w-[80px] outline-none text-xs bg-transparent px-1"
        />
        <button type="button" onClick={() => setOpen((o) => !o)} className="text-gray-400 hover:text-gray-600 text-xs">
          {open ? '▲' : '▼'}
        </button>
      </div>

      {open && (
        <div className="absolute z-30 mt-1 w-full min-w-[340px] bg-white border border-gray-200 rounded-xl shadow-xl max-h-80 overflow-hidden flex flex-col">
          <div className="p-2 border-b border-gray-100 flex flex-wrap gap-1 bg-slate-50">
            {categories.map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => setCategory(c)}
                className={`text-[10px] px-2 py-0.5 rounded-full border ${category === c ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-100'}`}
              >
                {c}
              </button>
            ))}
          </div>
          <div className="overflow-y-auto flex-1">
            {loading ? (
              <div className="p-3 text-xs text-gray-400 text-center">Loading…</div>
            ) : filtered.length === 0 ? (
              <div className="p-3 text-xs text-gray-400 text-center italic">No matches. Press <kbd className="border rounded px-1">Enter</kbd> to add "{query.toUpperCase()}" as a custom port.</div>
            ) : (
              filtered.map((p) => {
                const token = portToken(p);
                const picked = tokens.includes(token);
                return (
                  <button
                    type="button"
                    key={p.port_id}
                    onClick={() => addToken(token)}
                    className={`w-full text-left px-3 py-1.5 flex items-center gap-2 text-xs hover:bg-indigo-50 border-b border-gray-50 ${picked ? 'bg-emerald-50' : ''}`}
                  >
                    <span className="text-[10px] px-1.5 py-0.5 rounded border bg-white text-gray-600 border-gray-200 font-mono">{p.protocol || 'TCP'}</span>
                    <span className="text-[11px] font-semibold text-gray-800">{p.port === 0 ? '—' : p.port}</span>
                    <span className="text-[11px] text-gray-700 flex-1 truncate">{humanLabel(p)}</span>
                    <span className="text-[10px] text-indigo-600 bg-indigo-50 border border-indigo-100 rounded px-1.5 py-0.5">{p.category}</span>
                    {picked && <span className="text-[10px] text-emerald-700">✓ added</span>}
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
