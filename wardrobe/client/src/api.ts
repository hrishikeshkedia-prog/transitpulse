export interface WardrobeItem {
  id: string;
  name: string;
  category: 'top' | 'bottom' | 'shoes' | 'accessory' | 'outerwear' | 'dress';
  color: string;
  color_family: string;
  formality_min: number;
  formality_max: number;
  style_tags: string[];
  image_path: string | null;
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

const BASE = import.meta.env.DEV ? '' : '';

async function req<T>(method: string, path: string, body?: unknown, isForm = false): Promise<T> {
  const opts: RequestInit = { method };
  if (body) {
    if (isForm) {
      opts.body = body as FormData;
    } else {
      opts.headers = { 'Content-Type': 'application/json' };
      opts.body = JSON.stringify(body);
    }
  }
  const res = await fetch(BASE + path, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || res.statusText);
  return data as T;
}

export const api = {
  items: {
    list: (category?: string) =>
      req<WardrobeItem[]>('GET', `/api/items${category ? `?category=${category}` : ''}`),
    create: (form: FormData) =>
      req<WardrobeItem>('POST', '/api/items', form, true),
    update: (id: string, form: FormData) =>
      req<WardrobeItem>('PUT', `/api/items/${id}`, form, true),
    delete: (id: string) =>
      req<{ ok: boolean }>('DELETE', `/api/items/${id}`),
  },
  outfit: {
    recommend: (formalityLevel: number, description: string) =>
      req<OutfitResult>('POST', '/api/outfit/recommend', { formalityLevel, description }),
  },
};

export function imageUrl(filename: string | null): string | undefined {
  if (!filename) return undefined;
  return `/uploads/${filename}`;
}
