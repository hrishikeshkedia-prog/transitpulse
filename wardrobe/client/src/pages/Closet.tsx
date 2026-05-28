import { useState, useEffect, useCallback } from 'react';
import { api, WardrobeItem, imageUrl } from '../api';

const CATEGORIES = [
  { id: 'all',       label: 'All' },
  { id: 'top',       label: 'Tops' },
  { id: 'bottom',    label: 'Bottoms' },
  { id: 'shoes',     label: 'Shoes' },
  { id: 'dress',     label: 'Dresses' },
  { id: 'outerwear', label: 'Outerwear' },
  { id: 'accessory', label: 'Accessories' },
];

const EMOJI: Record<string, string> = {
  top: '👕', bottom: '👖', shoes: '👟', accessory: '👜', outerwear: '🧥', dress: '👗',
};

const FORMALITY = ['', 'Lounge', 'Casual', 'Smart', 'Business', 'Formal'];

function ItemSheet({ item, onClose, onDelete }: {
  item: WardrobeItem;
  onClose: () => void;
  onDelete: (id: string) => void;
}) {
  const [deleting, setDeleting] = useState(false);

  async function handleDelete() {
    if (!confirm(`Remove "${item.name}" from your wardrobe?`)) return;
    setDeleting(true);
    try {
      await api.items.delete(item.id);
      onDelete(item.id);
    } catch {
      setDeleting(false);
    }
  }

  const img = imageUrl(item.image_path);

  return (
    <div className="sheet-overlay" onClick={onClose}>
      <div className="sheet" onClick={e => e.stopPropagation()}>
        <div className="sheet-handle" />
        {img
          ? <img src={img} alt={item.name} className="sheet-img" />
          : <div className="sheet-img-ph">{EMOJI[item.category] ?? '👔'}</div>
        }
        <p className="sheet-name">{item.name}</p>
        <p className="sheet-meta">
          {item.category} · {item.color} · {FORMALITY[item.formality_min]}–{FORMALITY[item.formality_max]}
        </p>
        {item.style_tags.length > 0 && (
          <div className="sheet-tags">
            {item.style_tags.map(t => (
              <span key={t} className="bdg bg-b">{t}</span>
            ))}
          </div>
        )}
        {item.notes && <p className="sheet-notes">{item.notes}</p>}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <button className="btn btn-r btn-full" onClick={handleDelete} disabled={deleting}>
            {deleting ? 'Removing…' : 'Remove from Wardrobe'}
          </button>
          <button className="btn btn-gh btn-full" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}

export default function Closet() {
  const [category, setCategory] = useState('all');
  const [items, setItems] = useState<WardrobeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<WardrobeItem | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try { setItems(await api.items.list(category)); }
    finally { setLoading(false); }
  }, [category]);

  useEffect(() => { load(); }, [load]);

  function handleDelete(id: string) {
    setSelected(null);
    setItems(prev => prev.filter(i => i.id !== id));
  }

  const counts: Record<string, number> = { all: items.length };
  // Only relevant when showing "all" — this is the filtered count

  return (
    <main className="page">
      {/* Stats row */}
      {category === 'all' && items.length > 0 && (
        <div className="sg" style={{ marginBottom: '1rem' }}>
          <div className="stat">
            <div className="stat-lbl">Total Items</div>
            <div className="stat-val">{items.length}</div>
            <div className="stat-sub">in your closet</div>
          </div>
          <div className="stat">
            <div className="stat-lbl">Categories</div>
            <div className="stat-val mono">
              {new Set(items.map(i => i.category)).size}
            </div>
            <div className="stat-sub">types of clothing</div>
          </div>
        </div>
      )}

      <div className="cat-tabs">
        {CATEGORIES.map(cat => (
          <button
            key={cat.id}
            className={`cat-tab${category === cat.id ? ' active' : ''}`}
            onClick={() => setCategory(cat.id)}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="spinner" />
      ) : items.length === 0 ? (
        <div className="empty">
          <div className="empty-ic">👗</div>
          <p>Your closet is empty.<br />Tap <strong>Add Item</strong> below to get started.</p>
        </div>
      ) : (
        <div className="item-grid">
          {items.map(item => {
            const img = imageUrl(item.image_path);
            return (
              <div key={item.id} className="item-card" onClick={() => setSelected(item)}>
                {img
                  ? <img src={img} alt={item.name} className="item-card-img" />
                  : <div className="item-card-placeholder">{EMOJI[item.category] ?? '👔'}</div>
                }
                <div className="item-card-body">
                  <p className="item-card-name">{item.name}</p>
                  <p className="item-card-meta">
                    <span className="color-dot" style={{ background: item.color }} />
                    {item.category}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {selected && (
        <ItemSheet
          item={selected}
          onClose={() => setSelected(null)}
          onDelete={handleDelete}
        />
      )}
    </main>
  );
}
