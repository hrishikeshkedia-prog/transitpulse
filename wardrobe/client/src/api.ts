// All data stored locally in IndexedDB — no server needed.

export interface WardrobeItem {
  id: string;
  name: string;
  category: 'top' | 'bottom' | 'shoes' | 'accessory' | 'outerwear' | 'dress';
  color: string;
  color_family: string;
  formality_min: number;
  formality_max: number;
  style_tags: string[];
  image_data: string | null;
  notes: string;
  created_at: number;
}

export interface OutfitBase {
  type: 'dress' | 'top_bottom' | 'top_only' | 'bottom_only';
  dress?: WardrobeItem;
  top?: WardrobeItem;
  bottom?: WardrobeItem;
}

export interface OutfitResult {
  base: OutfitBase;
  shoes: WardrobeItem | null;
  accessories: WardrobeItem[];
  outerwear: WardrobeItem | null;
  keywords: string[];
}

// ── IndexedDB helpers ──────────────────────────────────────────

const DB_NAME = 'wardrobe';
const STORE = 'items';

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => {
      if (!req.result.objectStoreNames.contains(STORE)) {
        req.result.createObjectStore(STORE, { keyPath: 'id' });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

function idbGetAll<T>(db: IDBDatabase): Promise<T[]> {
  return new Promise((resolve, reject) => {
    const req = db.transaction(STORE, 'readonly').objectStore(STORE).getAll();
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

function idbGet<T>(db: IDBDatabase, id: string): Promise<T | undefined> {
  return new Promise((resolve, reject) => {
    const req = db.transaction(STORE, 'readonly').objectStore(STORE).get(id);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

function idbPut(db: IDBDatabase, item: WardrobeItem): Promise<void> {
  return new Promise((resolve, reject) => {
    const req = db.transaction(STORE, 'readwrite').objectStore(STORE).put(item);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

function idbDelete(db: IDBDatabase, id: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const req = db.transaction(STORE, 'readwrite').objectStore(STORE).delete(id);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

// ── Outfit engine ──────────────────────────────────────────────

const NEUTRAL_COLORS = new Set([
  'black', 'white', 'grey', 'gray', 'navy', 'beige', 'cream', 'tan',
  'brown', 'khaki', 'ivory', 'charcoal', 'taupe', 'camel', 'off-white',
  'stone', 'sand', 'champagne', 'ecru',
]);

const COLOR_WARMTH: Record<string, string> = {
  red: 'warm', orange: 'warm', yellow: 'warm', pink: 'warm',
  burgundy: 'warm', coral: 'warm', rust: 'warm', amber: 'warm',
  blue: 'cool', green: 'cool', purple: 'cool', teal: 'cool',
  mint: 'cool', lavender: 'cool', indigo: 'cool', olive: 'cool', sage: 'cool',
};

const STYLE_KEYWORD_MAP: Record<string, string[]> = {
  professional: ['professional', 'business', 'office', 'formal'],
  office: ['professional', 'business', 'office'],
  work: ['business', 'office', 'professional'],
  formal: ['formal', 'elegant', 'refined'],
  casual: ['casual', 'relaxed', 'everyday'],
  weekend: ['casual', 'relaxed', 'everyday'],
  date: ['elegant', 'romantic', 'stylish', 'chic'],
  dinner: ['elegant', 'stylish', 'smart'],
  night: ['elegant', 'stylish', 'chic', 'edgy'],
  club: ['edgy', 'stylish', 'bold'],
  beach: ['casual', 'summer', 'light'],
  summer: ['summer', 'light', 'casual'],
  vacation: ['casual', 'summer', 'relaxed'],
  sporty: ['sporty', 'athletic', 'active'],
  gym: ['athletic', 'sporty'],
  minimal: ['minimalist', 'clean', 'classic'],
  minimalist: ['minimalist', 'clean'],
  colorful: ['colorful', 'bold', 'vibrant'],
  bold: ['bold', 'colorful', 'statement'],
  classic: ['classic', 'timeless', 'preppy'],
  cozy: ['cozy', 'casual', 'relaxed'],
  smart: ['smart', 'polished', 'classic'],
  edgy: ['edgy', 'streetwear', 'bold'],
  streetwear: ['streetwear', 'edgy', 'casual'],
  boho: ['boho', 'eclectic', 'casual'],
  romantic: ['romantic', 'elegant', 'soft'],
  preppy: ['preppy', 'classic', 'smart'],
  vintage: ['vintage', 'classic', 'boho'],
};

function colorsOk(c1: string, c2: string): boolean {
  if (!c1 || !c2) return true;
  const a = c1.toLowerCase(), b = c2.toLowerCase();
  if (NEUTRAL_COLORS.has(a) || NEUTRAL_COLORS.has(b)) return true;
  const wa = COLOR_WARMTH[a], wb = COLOR_WARMTH[b];
  if (!wa || !wb) return true;
  return wa === wb;
}

function allOk(colors: string[]): boolean {
  for (let i = 0; i < colors.length; i++)
    for (let j = i + 1; j < colors.length; j++)
      if (!colorsOk(colors[i], colors[j])) return false;
  return true;
}

function parseKeywords(desc: string): string[] {
  const lower = desc.toLowerCase().replace(/[^a-z\s]/g, ' ');
  const tags = new Set<string>();
  for (const [kw, mapped] of Object.entries(STYLE_KEYWORD_MAP))
    if (lower.includes(kw.replace('_', ' '))) mapped.forEach(t => tags.add(t));
  return [...tags];
}

function score(item: WardrobeItem, keywords: string[]): number {
  return keywords.filter(kw => item.style_tags.includes(kw)).length;
}

function bestColorMatch(pool: WardrobeItem[], base: string[]): WardrobeItem | null {
  return pool.find(i => allOk([...base, i.color])) ?? pool[0] ?? null;
}

function recommendOutfit(items: WardrobeItem[], level: number, desc: string): OutfitResult | null {
  const keywords = parseKeywords(desc);
  const pool = items.filter(i => i.formality_min <= level && i.formality_max >= level);

  type Cat = WardrobeItem['category'];
  const by: Record<Cat, WardrobeItem[]> = { top: [], bottom: [], shoes: [], accessory: [], outerwear: [], dress: [] };
  for (const i of pool) by[i.category].push(i);
  for (const cat of Object.keys(by) as Cat[])
    by[cat].sort((a, b) => score(b, keywords) - score(a, keywords));

  let base: OutfitBase | null = null;
  let baseColors: string[] = [];

  if (by.dress.length) {
    base = { type: 'dress', dress: by.dress[0] };
    baseColors = [by.dress[0].color];
  } else if (by.top.length && by.bottom.length) {
    let best: { top: WardrobeItem; bottom: WardrobeItem } | null = null;
    let bestScore = -1;
    for (const top of by.top.slice(0, 8)) {
      for (const bottom of by.bottom.slice(0, 8)) {
        if (colorsOk(top.color, bottom.color)) {
          const s = score(top, keywords) + score(bottom, keywords);
          if (s > bestScore) { bestScore = s; best = { top, bottom }; }
        }
      }
    }
    if (!best) best = { top: by.top[0], bottom: by.bottom[0] };
    base = { type: 'top_bottom', ...best };
    baseColors = [best.top.color, best.bottom.color];
  } else if (by.top.length) {
    base = { type: 'top_only', top: by.top[0] };
    baseColors = [by.top[0].color];
  } else if (by.bottom.length) {
    base = { type: 'bottom_only', bottom: by.bottom[0] };
    baseColors = [by.bottom[0].color];
  }

  if (!base) return null;

  const shoes = bestColorMatch(by.shoes, baseColors);
  if (shoes) baseColors.push(shoes.color);

  const accessories: WardrobeItem[] = [];
  for (const acc of by.accessory) {
    if (accessories.length >= 2) break;
    if (allOk([...baseColors, acc.color])) accessories.push(acc);
  }

  const outerwear = bestColorMatch(by.outerwear, baseColors);
  return { base, shoes, accessories, outerwear, keywords };
}

// ── Public API (same interface as before) ─────────────────────

export const api = {
  items: {
    list: async (category?: string): Promise<WardrobeItem[]> => {
      const db = await openDB();
      const all = (await idbGetAll<WardrobeItem>(db)).sort((a, b) => b.created_at - a.created_at);
      return !category || category === 'all' ? all : all.filter(i => i.category === category);
    },
    create: async (body: Record<string, unknown>): Promise<WardrobeItem> => {
      const db = await openDB();
      const item: WardrobeItem = {
        id: crypto.randomUUID(),
        name: body.name as string,
        category: body.category as WardrobeItem['category'],
        color: body.color as string,
        color_family: body.color_family as string,
        formality_min: body.formality_min as number,
        formality_max: body.formality_max as number,
        style_tags: (body.style_tags as string[]) ?? [],
        image_data: (body.image_data as string | null) ?? null,
        notes: (body.notes as string) ?? '',
        created_at: Date.now(),
      };
      await idbPut(db, item);
      return item;
    },
    update: async (id: string, body: Record<string, unknown>): Promise<WardrobeItem> => {
      const db = await openDB();
      const existing = await idbGet<WardrobeItem>(db, id);
      if (!existing) throw new Error('Item not found');
      const updated = { ...existing, ...body, id } as WardrobeItem;
      await idbPut(db, updated);
      return updated;
    },
    delete: async (id: string): Promise<{ ok: boolean }> => {
      const db = await openDB();
      await idbDelete(db, id);
      return { ok: true };
    },
  },
  outfit: {
    recommend: async (formalityLevel: number, description: string): Promise<OutfitResult> => {
      const db = await openDB();
      const items = await idbGetAll<WardrobeItem>(db);
      const result = recommendOutfit(items, formalityLevel, description);
      if (!result) throw new Error('Not enough items for this formality level — add more clothes first!');
      return result;
    },
  },
};

export async function resizeImage(file: File, maxPx = 900): Promise<string> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      URL.revokeObjectURL(url);
      let { width, height } = img;
      if (width > height) {
        if (width > maxPx) { height = Math.round(height * maxPx / width); width = maxPx; }
      } else {
        if (height > maxPx) { width = Math.round(width * maxPx / height); height = maxPx; }
      }
      const canvas = document.createElement('canvas');
      canvas.width = width; canvas.height = height;
      canvas.getContext('2d')!.drawImage(img, 0, 0, width, height);
      resolve(canvas.toDataURL('image/jpeg', 0.82));
    };
    img.onerror = reject;
    img.src = url;
  });
}
