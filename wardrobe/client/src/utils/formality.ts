// Infers a [min, max] formality range from item name + category keywords.
// Returns null when there's not enough signal — user sets manually.
export function detectFormality(name: string, category: string): [number, number] | null {
  const n = name.toLowerCase();

  // Black-tie / ultra formal
  if (/tuxedo|black.?tie|evening gown|ball gown|dinner jacket/.test(n)) return [5, 5];

  // Formal
  if (/\bsuit\b|blazer|dress shirt|oxford shirt|formal trouser|pencil skirt|dress shoe|oxford shoe|pump|stiletto|court shoe/.test(n)) return [4, 5];

  // Business / smart casual
  if (/chino|button.?up|button.?down|\bpolo\b|blouse|slacks|dress pant|midi skirt|knee.?length|brogue|derby|chelsea boot|ankle boot|loafer/.test(n)) return [3, 4];

  // Casual
  if (/\bjeans?\b|denim|t.?shirt|\btee\b|casual|sneaker|trainer|runner|hoodie|sweatshirt|jumper|cardigan|\bshorts?\b|maxi dress|sundress/.test(n)) return [2, 3];

  // Loungewear / sport
  if (/pyjama|pajama|\bpjs?\b|sweatpant|jogger|slipper|lounge|tracksuit|legging|\bgym\b|athletic|sports?wear/.test(n)) return [1, 2];

  // Category-level fallbacks (broad ranges)
  if (category === 'shoes') return null;
  if (category === 'accessory') return null;
  if (category === 'outerwear') return null;
  if (category === 'dress') return [3, 5];

  return null;
}
