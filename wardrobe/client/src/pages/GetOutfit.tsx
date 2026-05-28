import { useState } from 'react';
import { api, OutfitResult, WardrobeItem, imageUrl } from '../api';

const FORMALITY_OPTIONS = [
  { value: 1, title: 'Loungewear',    desc: 'Homebody mode — comfort is king.' },
  { value: 2, title: 'Casual',        desc: 'Everyday errands, friends, weekend.' },
  { value: 3, title: 'Smart Casual',  desc: 'Nice restaurant, casual office, date.' },
  { value: 4, title: 'Business',      desc: 'Work meeting, interview, client lunch.' },
  { value: 5, title: 'Formal',        desc: 'Wedding, gala, black-tie event.' },
];

const EMOJI: Record<string, string> = {
  top: '👕', bottom: '👖', shoes: '👟', accessory: '👜', outerwear: '🧥', dress: '👗',
};

function OutfitPiece({ role, item }: { role: string; item: WardrobeItem }) {
  const img = imageUrl(item.image_path);
  return (
    <div className="outfit-piece">
      {img
        ? <img src={img} alt={item.name} className="outfit-piece-img" />
        : <div className="outfit-piece-placeholder">{EMOJI[item.category] ?? '👔'}</div>
      }
      <div>
        <p className="outfit-piece-role">{role}</p>
        <p className="outfit-piece-name">{item.name}</p>
        <p className="outfit-piece-sub">{item.color} · {item.category}</p>
      </div>
    </div>
  );
}

export default function GetOutfit() {
  const [formality, setFormality] = useState<number | null>(null);
  const [description, setDescription] = useState('');
  const [result, setResult] = useState<OutfitResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleGenerate() {
    if (!formality) { setError('Select a formality level first.'); return; }
    setLoading(true); setError(''); setResult(null);
    try {
      setResult(await api.outfit.recommend(formality, description));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not generate outfit');
    } finally {
      setLoading(false);
    }
  }

  if (result) {
    return (
      <main className="page">
        <div className="card">
          <div className="ch">
            <span className="ct">Your Outfit</span>
            <span className="bdg bg-b">{FORMALITY_OPTIONS.find(f => f.value === formality)?.title}</span>
          </div>
          <div className="cb" style={{ paddingBottom: 6 }}>
            {result.keywords.length > 0 && (
              <div className="kw-bar">
                {result.keywords.map(kw => <span key={kw} className="kw-chip">{kw}</span>)}
              </div>
            )}

            {result.base.type === 'dress' && result.base.dress && (
              <OutfitPiece role="Dress / Jumpsuit" item={result.base.dress} />
            )}
            {result.base.top && (
              <OutfitPiece role="Top" item={result.base.top} />
            )}
            {result.base.bottom && (
              <OutfitPiece role="Bottom" item={result.base.bottom} />
            )}
            {result.shoes && (
              <OutfitPiece role="Shoes" item={result.shoes} />
            )}
            {result.outerwear && (
              <OutfitPiece role="Outerwear" item={result.outerwear} />
            )}
            {result.accessories.map((acc, i) => (
              <OutfitPiece
                key={acc.id}
                role={`Accessory${result.accessories.length > 1 ? ` ${i + 1}` : ''}`}
                item={acc}
              />
            ))}
          </div>
        </div>

        <button className="btn btn-p btn-full" onClick={handleGenerate} disabled={loading}>
          {loading ? 'Trying another…' : 'Try Another Combination'}
        </button>
        <div style={{ height: 8 }} />
        <button className="btn btn-full" onClick={() => { setResult(null); setError(''); }}>
          Start Over
        </button>
      </main>
    );
  }

  return (
    <main className="page">
      {error && <div className="err-box">{error}</div>}

      {/* Formality */}
      <div className="card">
        <div className="ch"><span className="ct">Where are you going?</span></div>
        <div className="cb" style={{ paddingBottom: 6 }}>
          {FORMALITY_OPTIONS.map(opt => (
            <div
              key={opt.value}
              className={`formality-option${formality === opt.value ? ' selected' : ''}`}
              onClick={() => { setFormality(opt.value); setError(''); }}
            >
              <p className="fo-title">{opt.title}</p>
              <p className="fo-desc">{opt.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Vibe */}
      <div className="card">
        <div className="ch">
          <span className="ct">Describe your vibe</span>
          <span style={{ fontSize: 11, color: 'var(--tx3)' }}>optional</span>
        </div>
        <div className="cb">
          <div className="fg" style={{ marginBottom: 0 }}>
            <textarea
              placeholder="e.g. minimal and clean, colorful summer look, romantic date night, classic business…"
              value={description}
              onChange={e => setDescription(e.target.value)}
            />
          </div>
        </div>
      </div>

      <button
        className="btn btn-p btn-full"
        onClick={handleGenerate}
        disabled={loading || !formality}
      >
        {loading ? 'Building your outfit…' : 'Build My Outfit'}
      </button>

      {loading && <div className="spinner" />}
    </main>
  );
}
