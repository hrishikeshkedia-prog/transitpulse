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
