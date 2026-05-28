import { useState } from 'react';
import { api, OutfitResult, WardrobeItem, imageUrl } from '../api';

const FORMALITY_OPTIONS = [
  { value: 1, title: 'Loungewear', desc: 'Homebody mode. Comfort is king.' },
  { value: 2, title: 'Casual',     desc: 'Everyday errands, friends, weekend.' },
  { value: 3, title: 'Smart Casual', desc: 'Nice restaurant, casual office, date.' },
  { value: 4, title: 'Business',   desc: 'Work meeting, interview, client lunch.' },
  { value: 5, title: 'Formal',     desc: 'Wedding, gala, black-tie event.' },
];

const CATEGORY_EMOJI: Record<string, string> = {
  top: '👕', bottom: '👖', shoes: '👟', accessory: '👜', outerwear: '🧥', dress: '👗',
};

function OutfitPiece({ role, item }: { role: string; item: WardrobeItem }) {
  const img = imageUrl(item.image_path);
  return (
    <div className="outfit-piece">
      {img
        ? <img src={img} alt={item.name} className="outfit-piece-img" />
        : <div className="outfit-piece-placeholder">{CATEGORY_EMOJI[item.category] || '👔'}</div>
      }
      <div className="outfit-piece-info">
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
    if (!formality) { setError('Please select a formality level.'); return; }
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const r = await api.outfit.recommend(formality, description);
      setResult(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not generate outfit');
    } finally {
      setLoading(false);
    }
  }

  function handleNewOutfit() {
    setResult(null);
    setError('');
  }

  return (
    <main className="page">
      {!result ? (
        <>
          <p className="section-title">Where are you going?</p>
          <div className="formality-selector">
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

          <p className="section-title">Describe your vibe (optional)</p>
          <textarea
            className="form-textarea"
            placeholder="e.g. minimal and clean, date night, colorful summer look, classic business…"
            value={description}
            onChange={e => setDescription(e.target.value)}
            style={{ marginBottom: 20 }}
          />

          {error && <div className="error-msg">{error}</div>}

          <button
            className="btn btn-primary"
            onClick={handleGenerate}
            disabled={loading || !formality}
          >
            {loading ? 'Building your outfit…' : 'Build My Outfit'}
          </button>

          {loading && <div className="spinner" />}
        </>
      ) : (
        <>
          <p className="section-title" style={{ marginBottom: 8 }}>Your outfit</p>

          {result.keywords.length > 0 && (
            <div className="keywords-bar">
              {result.keywords.map(kw => <span key={kw} className="kw-chip">{kw}</span>)}
            </div>
          )}

          <div className="outfit-result">
            {result.base.type === 'dress' && result.base.dress && (
              <OutfitPiece role="Dress / Jumpsuit" item={result.base.dress} />
            )}
            {result.base.type === 'top_bottom' && result.base.top && (
              <OutfitPiece role="Top" item={result.base.top} />
            )}
            {result.base.type === 'top_bottom' && result.base.bottom && (
              <OutfitPiece role="Bottom" item={result.base.bottom} />
            )}
            {result.base.type === 'top_only' && result.base.top && (
              <OutfitPiece role="Top" item={result.base.top} />
            )}
            {result.base.type === 'bottom_only' && result.base.bottom && (
              <OutfitPiece role="Bottom" item={result.base.bottom} />
            )}
            {result.shoes && (
              <OutfitPiece role="Shoes" item={result.shoes} />
            )}
            {result.outerwear && (
              <OutfitPiece role="Outerwear" item={result.outerwear} />
            )}
            {result.accessories.map((acc, i) => (
              <OutfitPiece key={acc.id} role={`Accessory ${result.accessories.length > 1 ? i + 1 : ''}`} item={acc} />
            ))}
          </div>

          <div style={{ marginTop: 20, display: 'flex', flexDirection: 'column', gap: 10 }}>
            <button className="btn btn-accent" onClick={handleGenerate}>
              Try Another Combo
            </button>
            <button className="btn btn-ghost" onClick={handleNewOutfit}>
              Start Over
            </button>
          </div>
        </>
      )}
    </main>
  );
}
