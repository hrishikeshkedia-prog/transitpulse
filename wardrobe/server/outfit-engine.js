'use strict';

const NEUTRAL_COLORS = new Set([
  'black', 'white', 'grey', 'gray', 'navy', 'beige', 'cream', 'tan',
  'brown', 'khaki', 'ivory', 'charcoal', 'taupe', 'camel', 'off-white',
  'stone', 'sand', 'champagne', 'ecru',
]);

const COLOR_WARMTH = {
  red: 'warm', orange: 'warm', yellow: 'warm', pink: 'warm',
  burgundy: 'warm', coral: 'warm', salmon: 'warm', peach: 'warm',
  gold: 'warm', rust: 'warm', terracotta: 'warm', maroon: 'warm',
  rose: 'warm', magenta: 'warm', fuchsia: 'warm', amber: 'warm',
  blue: 'cool', green: 'cool', purple: 'cool', teal: 'cool',
  mint: 'cool', lavender: 'cool', indigo: 'cool', violet: 'cool',
  cyan: 'cool', turquoise: 'cool', olive: 'cool', sage: 'cool',
  cobalt: 'cool', emerald: 'cool', forest: 'cool', lilac: 'cool',
};

const STYLE_KEYWORD_MAP = {
  professional: ['professional', 'business', 'office', 'formal'],
  office: ['professional', 'business', 'office'],
  work: ['business', 'office', 'professional'],
  meeting: ['professional', 'business', 'formal'],
  formal: ['formal', 'elegant', 'refined'],
  black_tie: ['formal', 'elegant', 'refined'],
  gala: ['formal', 'elegant'],
  casual: ['casual', 'relaxed', 'everyday'],
  weekend: ['casual', 'relaxed', 'everyday'],
  chill: ['casual', 'relaxed'],
  laid_back: ['casual', 'relaxed'],
  date: ['elegant', 'romantic', 'stylish', 'chic'],
  dinner: ['elegant', 'stylish', 'smart'],
  night: ['elegant', 'stylish', 'chic', 'edgy'],
  club: ['edgy', 'stylish', 'bold'],
  beach: ['casual', 'summer', 'light'],
  summer: ['summer', 'light', 'casual'],
  vacation: ['casual', 'summer', 'relaxed'],
  sporty: ['sporty', 'athletic', 'active'],
  gym: ['athletic', 'sporty'],
  athletic: ['athletic', 'sporty', 'active'],
  minimal: ['minimalist', 'clean', 'classic'],
  minimalist: ['minimalist', 'clean'],
  colorful: ['colorful', 'bold', 'vibrant'],
  bold: ['bold', 'colorful', 'statement'],
  classic: ['classic', 'timeless', 'preppy'],
  cozy: ['cozy', 'casual', 'relaxed'],
  warm: ['cozy', 'casual'],
  smart: ['smart', 'polished', 'classic'],
  edgy: ['edgy', 'streetwear', 'bold'],
  streetwear: ['streetwear', 'edgy', 'casual'],
  boho: ['boho', 'eclectic', 'casual'],
  bohemian: ['boho', 'eclectic'],
  romantic: ['romantic', 'elegant', 'soft'],
  preppy: ['preppy', 'classic', 'smart'],
  vintage: ['vintage', 'classic', 'boho'],
  retro: ['vintage', 'classic'],
};

function colorsCompatible(c1, c2) {
  if (!c1 || !c2) return true;
  const lc1 = c1.toLowerCase();
  const lc2 = c2.toLowerCase();
  if (NEUTRAL_COLORS.has(lc1) || NEUTRAL_COLORS.has(lc2)) return true;
  const w1 = COLOR_WARMTH[lc1];
  const w2 = COLOR_WARMTH[lc2];
  if (!w1 || !w2) return true;
  return w1 === w2;
}

function allColorsCompatible(colors) {
  for (let i = 0; i < colors.length; i++) {
    for (let j = i + 1; j < colors.length; j++) {
      if (!colorsCompatible(colors[i], colors[j])) return false;
    }
  }
  return true;
}

function parseKeywords(description) {
  const lower = description.toLowerCase().replace(/[^a-z\s]/g, ' ');
  const tags = new Set();
  for (const [keyword, mapped] of Object.entries(STYLE_KEYWORD_MAP)) {
    const kw = keyword.replace('_', ' ');
    if (lower.includes(kw)) {
      mapped.forEach(t => tags.add(t));
    }
  }
  return [...tags];
}

function scoreItem(item, keywords) {
  if (!keywords.length) return 0;
  const itemTags = JSON.parse(item.style_tags || '[]');
  let score = 0;
  for (const kw of keywords) {
    if (itemTags.includes(kw)) score++;
  }
  return score;
}

function pickBestColorMatch(candidates, baseColors) {
  const compatible = candidates.filter(item =>
    allColorsCompatible([...baseColors, item.color])
  );
  return compatible.length ? compatible[0] : (candidates[0] || null);
}

function recommend(items, formalityLevel, description) {
  const keywords = parseKeywords(description);

  const compatible = items.filter(item =>
    item.formality_min <= formalityLevel && item.formality_max >= formalityLevel
  );

  const byCategory = {
    top: [], bottom: [], shoes: [], accessory: [], outerwear: [], dress: [],
  };
  for (const item of compatible) {
    const cat = item.category;
    if (byCategory[cat]) byCategory[cat].push(item);
  }

  for (const cat of Object.keys(byCategory)) {
    byCategory[cat].forEach(item => { item._score = scoreItem(item, keywords); });
    byCategory[cat].sort((a, b) => b._score - a._score);
  }

  let base = null;
  let baseColors = [];

  if (byCategory.dress.length) {
    const piece = byCategory.dress[0];
    base = { type: 'dress', dress: piece };
    baseColors = [piece.color];
  } else if (byCategory.top.length && byCategory.bottom.length) {
    let best = null;
    let bestScore = -1;
    for (const top of byCategory.top.slice(0, 8)) {
      for (const bottom of byCategory.bottom.slice(0, 8)) {
        if (colorsCompatible(top.color, bottom.color)) {
          const score = top._score + bottom._score;
          if (score > bestScore) { bestScore = score; best = { top, bottom }; }
        }
      }
    }
    if (!best) best = { top: byCategory.top[0], bottom: byCategory.bottom[0] };
    base = { type: 'top_bottom', top: best.top, bottom: best.bottom };
    baseColors = [best.top.color, best.bottom.color];
  } else if (byCategory.top.length) {
    base = { type: 'top_only', top: byCategory.top[0] };
    baseColors = [byCategory.top[0].color];
  } else if (byCategory.bottom.length) {
    base = { type: 'bottom_only', bottom: byCategory.bottom[0] };
    baseColors = [byCategory.bottom[0].color];
  }

  if (!base) return null;

  const shoes = pickBestColorMatch(byCategory.shoes, baseColors);
  if (shoes) baseColors.push(shoes.color);

  const accessories = [];
  for (const acc of byCategory.accessory) {
    if (accessories.length >= 2) break;
    if (allColorsCompatible([...baseColors, acc.color])) {
      accessories.push(acc);
    }
  }

  const outerwear = pickBestColorMatch(byCategory.outerwear, baseColors);

  return { base, shoes, accessories, outerwear, keywords };
}

module.exports = { recommend };
