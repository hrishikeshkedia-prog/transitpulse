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

async function req<T>(method: string, path: string, body?: unknown): Promise<T> {
  const opts: RequestInit = { method };
  if (body !== undefined) {
    opts.headers = { 'Content-Type': 'application/json' };
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(path, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || res.statusText);
  return data as T;
}

export const api = {
  items: {
    list: (category?: string) =>
      req<WardrobeItem[]>('GET', `/api/items${category ? `?category=${category}` : ''}`),
    create: (body: Record<string, unknown>) =>
      req<WardrobeItem>('POST', '/api/items', body),
    update: (id: string, body: Record<string, unknown>) =>
      req<WardrobeItem>('PUT', `/api/items/${id}`, body),
    delete: (id: string) =>
      req<{ ok: boolean }>('DELETE', `/api/items/${id}`),
  },
  outfit: {
    recommend: (formalityLevel: number, description: string) =>
      req<OutfitResult>('POST', '/api/outfit/recommend', { formalityLevel, description }),
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
