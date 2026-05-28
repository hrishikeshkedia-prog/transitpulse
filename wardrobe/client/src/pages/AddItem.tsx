import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';

const CATEGORIES = [
  { value: 'top',       label: 'Top (shirt, t-shirt, blouse…)' },
  { value: 'bottom',    label: 'Bottom (pants, jeans, skirt…)' },
  { value: 'dress',     label: 'Dress / Jumpsuit' },
  { value: 'shoes',     label: 'Shoes / Sneakers / Boots' },
  { value: 'outerwear', label: 'Outerwear (jacket, coat…)' },
  { value: 'accessory', label: 'Accessory (bag, hat, belt…)' },
];

const COLORS: { name: string; hex: string; family: string }[] = [
  { name: 'black',    hex: '#111111', family: 'neutral' },
  { name: 'white',    hex: '#f5f5f5', family: 'neutral' },
  { name: 'grey',     hex: '#9ca3af', family: 'neutral' },
  { name: 'navy',     hex: '#1e3a5f', family: 'neutral' },
  { name: 'beige',    hex: '#d4b896', family: 'neutral' },
  { name: 'brown',    hex: '#7c4f2e', family: 'neutral' },
  { name: 'camel',    hex: '#c19a6b', family: 'neutral' },
  { name: 'khaki',    hex: '#c3b091', family: 'neutral' },
  { name: 'red',      hex: '#dc2626', family: 'warm' },
  { name: 'pink',     hex: '#ec4899', family: 'warm' },
  { name: 'orange',   hex: '#f97316', family: 'warm' },
  { name: 'yellow',   hex: '#eab308', family: 'warm' },
  { name: 'burgundy', hex: '#7c1d3f', family: 'warm' },
  { name: 'coral',    hex: '#f87171', family: 'warm' },
  { name: 'blue',     hex: '#3b82f6', family: 'cool' },
  { name: 'green',    hex: '#22c55e', family: 'cool' },
  { name: 'purple',   hex: '#a855f7', family: 'cool' },
  { name: 'teal',     hex: '#14b8a6', family: 'cool' },
  { name: 'olive',    hex: '#717700', family: 'cool' },
  { name: 'lavender', hex: '#c4b5fd', family: 'cool' },
  { name: 'mint',     hex: '#6ee7b7', family: 'cool' },
  { name: 'indigo',   hex: '#4338ca', family: 'cool' },
  { name: 'rust',     hex: '#c2410c', family: 'warm' },
  { name: 'sage',     hex: '#87a878', family: 'cool' },
];

const FORMALITY_LEVELS = [
  { value: 1, label: 'Lounge', desc: 'PJs, sweats' },
  { value: 2, label: 'Casual', desc: 'Everyday' },
  { value: 3, label: 'Smart',  desc: 'Smart casual' },
  { value: 4, label: 'Business', desc: 'Work' },
  { value: 5, label: 'Formal', desc: 'Events' },
];

const ALL_TAGS = [
  'casual', 'relaxed', 'classic', 'minimalist', 'bold', 'colorful',
  'sporty', 'athletic', 'elegant', 'romantic', 'edgy', 'streetwear',
  'business', 'professional', 'boho', 'preppy', 'cozy', 'summer',
  'vintage', 'timeless', 'chic', 'statement',
];

export default function AddItem() {
  const navigate = useNavigate();
  const fileRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState('');
  const [category, setCategory] = useState('top');
  const [color, setColor] = useState('black');
  const [formalityRange, setFormalityRange] = useState<[number, number]>([1, 5]);
  const [tags, setTags] = useState<string[]>([]);
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    const reader = new FileReader();
    reader.onload = ev => setPreview(ev.target?.result as string);
    reader.readAsDataURL(f);
  }

  function toggleTag(tag: string) {
    setTags(prev => prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]);
  }

  function toggleFormality(val: number) {
    const [min, max] = formalityRange;
    if (val < min) setFormalityRange([val, max]);
    else if (val > max) setFormalityRange([min, val]);
    else if (val === min && val === max) return;
    else if (val === min) setFormalityRange([min + 1, max]);
    else if (val === max) setFormalityRange([min, max - 1]);
    else setFormalityRange([val, val]);
  }

  const isFSel = (v: number) => v >= formalityRange[0] && v <= formalityRange[1];

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) { setError('Please enter a name.'); return; }
    setSaving(true); setError('');
    try {
      const colorObj = COLORS.find(c => c.name === color);
      const form = new FormData();
      form.append('name', name.trim());
      form.append('category', category);
      form.append('color', color);
      form.append('color_family', colorObj?.family ?? 'neutral');
      form.append('formality_min', String(formalityRange[0]));
      form.append('formality_max', String(formalityRange[1]));
      form.append('style_tags', JSON.stringify(tags));
      form.append('notes', notes.trim());
      if (file) form.append('image', file);
      await api.items.create(form);
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save');
      setSaving(false);
    }
  }

  const selectedColor = COLORS.find(c => c.name === color);

  return (
    <main className="page">
      <form onSubmit={handleSubmit}>
        {error && <div className="err-box">{error}</div>}

        {/* Photo */}
        <div className="card">
          <div className="ch"><span className="ct">Photo</span><span style={{ fontSize: 11, color: 'var(--tx3)' }}>optional</span></div>
          <div className="cb">
            <div className="img-upload" onClick={() => fileRef.current?.click()}>
              {preview
                ? <img src={preview} alt="preview" />
                : <div className="img-upload-hint">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                      <polyline points="17,8 12,3 7,8"/>
                      <line x1="12" y1="3" x2="12" y2="15"/>
                    </svg>
                    <span>Tap to upload or take photo</span>
                  </div>
              }
              <input ref={fileRef} type="file" accept="image/*" capture="environment" style={{ display: 'none' }} onChange={handleFileChange} />
            </div>
          </div>
        </div>

        {/* Details */}
        <div className="card">
          <div className="ch"><span className="ct">Details</span></div>
          <div className="cb">
            <div className="fg">
              <label>Name</label>
              <input type="text" placeholder="e.g. White Oxford Shirt" value={name} onChange={e => setName(e.target.value)} required />
            </div>
            <div className="fg">
              <label>Category</label>
              <select value={category} onChange={e => setCategory(e.target.value)}>
                {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </div>
            <div className="fg">
              <label>Notes</label>
              <textarea placeholder="Brand, size, where you got it…" value={notes} onChange={e => setNotes(e.target.value)} />
            </div>
          </div>
        </div>

        {/* Color */}
        <div className="card">
          <div className="ch">
            <span className="ct">Colour</span>
            {selectedColor && (
              <span className="bdg bg-gr" style={{ textTransform: 'capitalize' }}>{selectedColor.name}</span>
            )}
          </div>
          <div className="cb">
            <div className="color-grid">
              {COLORS.map(c => (
                <button
                  key={c.name}
                  type="button"
                  className={`color-swatch${color === c.name ? ' selected' : ''}`}
                  style={{ background: c.hex, border: c.name === 'white' ? '2px solid var(--bd)' : undefined }}
                  onClick={() => setColor(c.name)}
                  title={c.name}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Formality */}
        <div className="card">
          <div className="ch">
            <span className="ct">Formality Range</span>
            <span style={{ fontSize: 11, color: 'var(--tx3)' }}>tap to toggle</span>
          </div>
          <div className="cb">
            <div className="formality-row">
              {FORMALITY_LEVELS.map(f => (
                <button
                  key={f.value}
                  type="button"
                  className={`formality-btn${isFSel(f.value) ? ' selected' : ''}`}
                  onClick={() => toggleFormality(f.value)}
                >
                  {f.label}
                  <br />
                  <span style={{ fontWeight: 400, fontSize: 10 }}>{f.desc}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Style tags */}
        <div className="card">
          <div className="ch"><span className="ct">Style Tags</span><span style={{ fontSize: 11, color: 'var(--tx3)' }}>optional</span></div>
          <div className="cb">
            <div className="tags-wrap">
              {ALL_TAGS.map(tag => (
                <button
                  key={tag}
                  type="button"
                  className={`tag-chip${tags.includes(tag) ? ' selected' : ''}`}
                  onClick={() => toggleTag(tag)}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>
        </div>

        <button type="submit" className="btn btn-p btn-full" disabled={saving}>
          {saving ? 'Saving…' : 'Add to Wardrobe'}
        </button>
        <div style={{ height: 8 }} />
      </form>
    </main>
  );
}
