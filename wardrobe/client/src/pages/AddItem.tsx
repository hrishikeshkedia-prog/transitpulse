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
  { name: 'black',      hex: '#111111', family: 'neutral' },
  { name: 'white',      hex: '#f8f8f8', family: 'neutral' },
  { name: 'grey',       hex: '#9ca3af', family: 'neutral' },
  { name: 'navy',       hex: '#1e3a5f', family: 'neutral' },
  { name: 'beige',      hex: '#d4b896', family: 'neutral' },
  { name: 'brown',      hex: '#7c4f2e', family: 'neutral' },
  { name: 'camel',      hex: '#c19a6b', family: 'neutral' },
  { name: 'khaki',      hex: '#c3b091', family: 'neutral' },
  { name: 'red',        hex: '#dc2626', family: 'warm' },
  { name: 'pink',       hex: '#ec4899', family: 'warm' },
  { name: 'orange',     hex: '#f97316', family: 'warm' },
  { name: 'yellow',     hex: '#eab308', family: 'warm' },
  { name: 'burgundy',   hex: '#7c1d3f', family: 'warm' },
  { name: 'coral',      hex: '#f87171', family: 'warm' },
  { name: 'blue',       hex: '#3b82f6', family: 'cool' },
  { name: 'green',      hex: '#22c55e', family: 'cool' },
  { name: 'purple',     hex: '#a855f7', family: 'cool' },
  { name: 'teal',       hex: '#14b8a6', family: 'cool' },
  { name: 'olive',      hex: '#717700', family: 'cool' },
  { name: 'lavender',   hex: '#c4b5fd', family: 'cool' },
  { name: 'mint',       hex: '#6ee7b7', family: 'cool' },
  { name: 'indigo',     hex: '#4338ca', family: 'cool' },
  { name: 'rust',       hex: '#c2410c', family: 'warm' },
  { name: 'sage',       hex: '#87a878', family: 'cool' },
];

const FORMALITY_LEVELS = [
  { value: 1, label: 'Lounge', desc: 'PJs, sweats' },
  { value: 2, label: 'Casual', desc: 'Everyday' },
  { value: 3, label: 'Smart', desc: 'Smart casual' },
  { value: 4, label: 'Business', desc: 'Work ready' },
  { value: 5, label: 'Formal', desc: 'Events / gala' },
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
    if (val === min && val === max) return;
    if (val < min) setFormalityRange([val, max]);
    else if (val > max) setFormalityRange([min, val]);
    else if (val === min) setFormalityRange([val + 1, max]);
    else if (val === max) setFormalityRange([min, val - 1]);
    else setFormalityRange([val, val]);
  }

  function isFormalitySelected(val: number) {
    return val >= formalityRange[0] && val <= formalityRange[1];
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) { setError('Please enter a name.'); return; }
    setSaving(true);
    setError('');
    try {
      const colorObj = COLORS.find(c => c.name === color);
      const form = new FormData();
      form.append('name', name.trim());
      form.append('category', category);
      form.append('color', color);
      form.append('color_family', colorObj?.family || 'neutral');
      form.append('formality_min', String(formalityRange[0]));
      form.append('formality_max', String(formalityRange[1]));
      form.append('style_tags', JSON.stringify(tags));
      form.append('notes', notes.trim());
      if (file) form.append('image', file);
      await api.items.create(form);
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save item');
      setSaving(false);
    }
  }

  const selectedColor = COLORS.find(c => c.name === color);

  return (
    <main className="page">
      <form onSubmit={handleSubmit}>
        {error && <div className="error-msg">{error}</div>}

        <div className="form-section">
          <label className="form-label">Photo</label>
          <div className="image-upload-area" onClick={() => fileRef.current?.click()}>
            {preview
              ? <img src={preview} alt="preview" />
              : <div className="upload-hint">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="17,8 12,3 7,8"/>
                    <line x1="12" y1="3" x2="12" y2="15"/>
                  </svg>
                  <span>Tap to upload a photo</span>
                  <span style={{ fontSize: 11 }}>optional</span>
                </div>
            }
            <input ref={fileRef} type="file" accept="image/*" capture="environment" style={{ display:'none' }} onChange={handleFileChange} />
          </div>
        </div>

        <div className="form-section">
          <label className="form-label">Name</label>
          <input
            className="form-input"
            type="text"
            placeholder="e.g. White Oxford Shirt"
            value={name}
            onChange={e => setName(e.target.value)}
            required
          />
        </div>

        <div className="form-section">
          <label className="form-label">Category</label>
          <select className="form-select" value={category} onChange={e => setCategory(e.target.value)}>
            {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
        </div>

        <div className="form-section">
          <label className="form-label">
            Color
            {selectedColor && (
              <span style={{ marginLeft: 8, fontWeight: 400, textTransform: 'capitalize', color: 'var(--text)' }}>
                — {selectedColor.name}
              </span>
            )}
          </label>
          <div className="color-grid">
            {COLORS.map(c => (
              <button
                key={c.name}
                type="button"
                className={`color-swatch${color === c.name ? ' selected' : ''}`}
                style={{ background: c.hex, border: c.name === 'white' ? '2px solid var(--border)' : undefined }}
                onClick={() => setColor(c.name)}
                title={c.name}
              />
            ))}
          </div>
        </div>

        <div className="form-section">
          <label className="form-label">Works for (formality range — tap to toggle)</label>
          <div className="formality-row">
            {FORMALITY_LEVELS.map(f => (
              <button
                key={f.value}
                type="button"
                className={`formality-btn${isFormalitySelected(f.value) ? ' selected' : ''}`}
                onClick={() => toggleFormality(f.value)}
              >
                {f.label}<br />
                <span style={{ fontWeight: 400, fontSize: 10 }}>{f.desc}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="form-section">
          <label className="form-label">Style tags (optional)</label>
          <div className="tags-grid">
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

        <div className="form-section">
          <label className="form-label">Notes (optional)</label>
          <textarea
            className="form-textarea"
            placeholder="Brand, size, where you got it…"
            value={notes}
            onChange={e => setNotes(e.target.value)}
          />
        </div>

        <button type="submit" className="btn btn-primary" disabled={saving}>
          {saving ? 'Saving…' : 'Add to Wardrobe'}
        </button>
      </form>
    </main>
  );
}
