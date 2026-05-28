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

const CATEGORY_EMOJI: Record<string, string> = {
  top: '👕', bottom: '👖', shoes: '👟', accessory: '👜', outerwear: '🧥', dress: '👗',
};

const FORMALITY_LABELS = ['', 'Loungewear', 'Casual', 'Smart Casual', 'Business', 'Formal'];

function ItemDetail({ item, onClose, onDelete }: {
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
          : <div className="sheet-img" style={{ display:'flex',alignItems:'center',justifyContent:'center',fontSize:64 }}>{CATEGORY_EMOJI[item.category] || '👔'}</div>
        }
        <p className="sheet-title">{item.name}</p>
        <p className="sheet-meta">
          {item.category} · {item.color} · {FORMALITY_LABELS[item.formality_min]}–{FORMALITY_LABELS[item.formality_max]}
        </p>
        {item.style_tags.length > 0 && (
          <div className="sheet-tags">
            {item.style_tags.map(t => <span key={t} className="sheet-tag">{t}</span>)}
          </div>
        )}
        {item.notes && <p className="sheet-notes">{item.notes}</p>}
        <button className="btn btn-danger" onClick={handleDelete} disabled={deleting}>
          {deleting ? 'Removing…' : 'Remove from Wardrobe'}
        </button>
        <button className="btn btn-ghost" style={{ marginTop: 8 }} onClick={onClose}>Close</button>
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
    try {
      const data = await api.items.list(category);
      setItems(data);
    } finally {
      setLoading(false);
    }
  }, [category]);

  useEffect(() => { load(); }, [load]);

  function handleDelete(id: string) {
    setSelected(null);
    setItems(prev => prev.filter(i => i.id !== id));
  }

  return (
    <main className="page">
      <div className="category-tabs">
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
        <div className="empty-state">
          <div className="empty-icon">👗</div>
          <p>Your closet is empty.<br />Tap <strong>Add</strong> to upload your first item.</p>
        </div>
      ) : (
        <div className="item-grid">
          {items.map(item => {
            const img = imageUrl(item.image_path);
            return (
              <div key={item.id} className="item-card" onClick={() => setSelected(item)}>
                {img
                  ? <img src={img} alt={item.name} className="item-card-img" />
                  : <div className="item-card-img-placeholder">{CATEGORY_EMOJI[item.category] || '👔'}</div>
                }
                <div className="item-card-body">
                  <p className="item-card-name">{item.name}</p>
                  <p className="item-card-meta">
                    <span className="item-card-color-dot" style={{ background: item.color }} />
                    {item.category}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {selected && (
        <ItemDetail
          item={selected}
          onClose={() => setSelected(null)}
          onDelete={handleDelete}
        />
      )}
    </main>
  );
}
