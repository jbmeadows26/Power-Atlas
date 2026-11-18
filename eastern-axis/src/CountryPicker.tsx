import { useEffect, useRef, useState } from 'react';
import { ChevronDown, Search } from 'lucide-react';
type Entry = { code: string; name: string };
export default function CountryPicker({ countries, value, onChange }: {
  countries: Entry[];
  value: string;
  onChange: (code: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);
  const root = useRef<HTMLDivElement>(null);
  const searchInput = useRef<HTMLInputElement>(null);
  const current = countries.find(c => c.code === value);
  const entries: Entry[] = [{code:'all',name:'Global / regional'}, ...countries];
  const results = entries.filter(c => (
    c.name.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()) ||
    c.code.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase())
  ));
  useEffect(() => {
    if (!open) return;
    searchInput.current?.focus();
    const closeOnOutside = (event: PointerEvent) => {
      if (root.current && !root.current.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener('pointerdown', closeOnOutside);
    return () => document.removeEventListener('pointerdown', closeOnOutside);
  }, [open]);
  const choose = (code: string) => {
    onChange(code);
    setOpen(false);
    setQuery('');
    setActiveIndex(0);
  };
  return (
    <div className="ea-context" ref={root}>
      <label htmlFor="ea-country-scope">COUNTRY CONTEXT</label>
      <button type="button" id="ea-country-scope" className="ea-picker-trigger"
        aria-label="Choose country intelligence scope" aria-expanded={open} aria-haspopup="listbox"
        onClick={() => { setOpen(v => !v); setQuery(''); setActiveIndex(0); }}>
        <span>{current?.name || 'Global / regional'}</span><ChevronDown size={17} aria-hidden="true" />
      </button>
      {open && (
        <div className="ea-picker-panel">
          <div className="ea-picker-search"><Search size={17} aria-hidden="true" />
            <input ref={searchInput} type="search" role="combobox"
              aria-label="Search country or code" aria-autocomplete="list"
              aria-expanded="true" aria-controls="ea-country-options"
              aria-activedescendant={results.length ? 'ea-scope-option-' + activeIndex : undefined}
              placeholder="Search country or ISO code…" value={query}
              onChange={e => { setQuery(e.target.value); setActiveIndex(0); }}
              onKeyDown={e => {
                if (e.key === 'Escape') { setOpen(false); e.preventDefault(); }
                if (e.key === 'ArrowDown') { setActiveIndex(i => Math.min(i+1,results.length-1)); e.preventDefault(); }
                if (e.key === 'ArrowUp') { setActiveIndex(i => Math.max(i-1,0)); e.preventDefault(); }
                if (e.key === 'Enter' && results[activeIndex]) { choose(results[activeIndex].code); e.preventDefault(); }
              }} />
          </div>
          <div className="ea-picker-results" id="ea-country-options" role="listbox" aria-label="Country intelligence scope options">
            {results.length === 0 ? <p className="ea-picker-empty">No matching countries</p> :
              results.map((c,i) => (
                <button type="button" role="option" id={'ea-scope-option-'+i} key={c.code}
                  className={'ea-picker-option '+(i===activeIndex?'ea-picker-active':'')}
                  aria-selected={value===c.code}
                  onMouseEnter={() => setActiveIndex(i)}
                  onClick={() => choose(c.code)}>
                  <span>{c.name}</span><small>{c.code==='all'?'GLOBAL':c.code}</small>
                </button>
              ))}
          </div>
          <p className="ea-picker-tip">Type to filter · ↑↓ to navigate · Enter to select</p>
        </div>
      )}
    </div>
  );
}
