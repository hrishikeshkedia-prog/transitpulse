# Wardrobe — Smart Outfit Recommender

> A mobile-first PWA that catalogues your clothes and recommends outfits using a hand-written algorithm based on color theory and formality scoring.

---

## The Idea

Most people open their wardrobe every morning and still can't decide what to wear — not because they have nothing, but because matching clothes is mentally taxing. I built this app to solve that: catalog your items once, describe where you're going, and get a styled outfit instantly.

No subscription. No AI API bill. The recommendation engine runs entirely on the server with logic I wrote myself.

---

## How It Works

The core is a recommendation engine (`server/outfit-engine.js`) with three layers:

### 1. Formality Filtering
Every item in the wardrobe is tagged with a `[min, max]` formality range on a 1–5 scale:

| Level | Description |
|---|---|
| 1 | Loungewear — sweats, PJs |
| 2 | Casual — everyday errands, friends |
| 3 | Smart Casual — nice restaurant, casual date |
| 4 | Business — work meeting, interview |
| 5 | Formal — wedding, gala, black-tie |

When you request an outfit at level 3, only items whose range overlaps with 3 are considered. A hoodie tagged `[1, 2]` is never suggested for a dinner.

### 2. Color Theory Matching
Colors are classified as **warm**, **cool**, or **neutral**:

- **Warm:** red, orange, yellow, pink, burgundy, coral, rust…
- **Cool:** blue, green, purple, teal, olive, lavender…
- **Neutral:** black, white, grey, navy, beige, tan… *(pair with anything)*

The engine only pairs items whose color families are compatible. A warm-toned top won't be combined with cool-toned trousers unless one of them is neutral. This is real fashion advice encoded as logic.

### 3. Style Keyword Scoring
Each item carries style tags (`casual`, `minimalist`, `edgy`, `romantic`, `preppy`…). When you describe your vibe — *"romantic date night"* or *"minimal and clean"* — the engine parses your description into style keywords and ranks compatible items by how many tags match, bubbling the best fit to the top.

---

## Features

- **Wardrobe Closet** — browse all your items with photos, color swatches, and formality badges
- **Add Item** — photo upload (or camera capture on mobile), color picker, formality range, style tags
- **Auto-formality detection** — type "Oxford Shirt" and the app detects `[4, 5]` automatically from the item name
- **Outfit Generator** — select formality level, optionally describe a vibe, get a complete outfit (top + bottom or dress, shoes, outerwear, up to 2 accessories)
- **Gender profiles** — men's and women's category sets with a one-tap wardrobe switch
- **PWA** — installable to home screen, offline-capable via service worker

---

## Tech Stack

```
Frontend     React 18, TypeScript, React Router v6, Vite
PWA          vite-plugin-pwa, Workbox service worker
Backend      Node.js, Express.js
Database     SQLite / better-sqlite3 (dev)  ·  PostgreSQL (production)
Build        Vite (bundles to client/dist, served by Express)
```

This is a different stack from my FreightDesk Pro app (vanilla JS) — I chose React + TypeScript here to work with a component model and static types for a data-rich UI.

---

## Architecture

```
wardrobe/
├── client/          React + TypeScript frontend (Vite)
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Closet.tsx        browse all items
│   │   │   ├── AddItem.tsx       add new clothing item
│   │   │   └── GetOutfit.tsx     outfit recommendation UI
│   │   ├── utils/
│   │   │   └── formality.ts      auto-detect formality from item name
│   │   └── api.ts                typed API client
│   └── dist/                     Vite build output (served by Express)
│
└── server/          Node.js + Express backend
    ├── outfit-engine.js   recommendation algorithm (no ML library)
    ├── db.js              dual PostgreSQL/SQLite adapter
    └── routes/
        ├── items.js       CRUD for wardrobe items
        └── outfits.js     recommendation endpoint
```

The Express server serves both the REST API and the built React app as a single deployable unit — no separate hosting needed.

---

## The Algorithm in Detail

The recommendation function (`recommend()` in `outfit-engine.js`) runs these steps:

1. **Filter by formality** — discard items whose range doesn't include the requested level
2. **Group by category** — separate tops, bottoms, dresses, shoes, accessories, outerwear
3. **Score by style keywords** — rank each group by tag-match count against the parsed vibe description
4. **Pick the base piece** — prefer a dress if available (single-piece outfit); otherwise find the best-scoring top+bottom pair whose colors are compatible
5. **Add shoes** — pick the highest-scoring shoe that's color-compatible with the base
6. **Add accessories** — up to 2, each checked for compatibility with all already-chosen colors
7. **Add outerwear** — same color-compatibility check

This is a deterministic, explainable algorithm. You can trace exactly why each item was chosen.

---

## Auto-Formality Detection

Rather than asking users to manually classify every new item, the `detectFormality()` function reads the item's name and infers a formality range using regex patterns:

```ts
if (/tuxedo|black.?tie|evening gown/.test(n))      return [5, 5];
if (/\bsuit\b|blazer|oxford shirt/.test(n))         return [4, 5];
if (/chino|button.?up|\bpolo\b|blouse/.test(n))     return [3, 4];
if (/\bjeans?\b|t.?shirt|hoodie|sneaker/.test(n))   return [2, 3];
if (/sweatpant|jogger|legging|\bgym\b/.test(n))     return [1, 2];
```

If a match is found, the UI shows an "auto-detected" badge and pre-fills the range — users can override with one tap.

---

## Running Locally

```bash
# Install and start everything
cd wardrobe
npm install         # install root deps if any
cd server && npm install
cd ../client && npm install && npm run build
cd ..
node server/index.js
# Open http://localhost:3800
```

**With PostgreSQL:**
```bash
DATABASE_URL=postgres://user:pass@localhost/wardrobe node server/index.js
```

**Frontend dev mode (hot reload):**
```bash
cd client && npm run dev
# Vite proxies API requests to the server
```

---

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/items` | List all wardrobe items |
| `POST` | `/api/items` | Add a new item |
| `PUT` | `/api/items/:id` | Update an item |
| `DELETE` | `/api/items/:id` | Remove an item |
| `POST` | `/api/outfit/recommend` | Get an outfit recommendation |
| `GET` | `/api/health` | Health check |

---

## What I Learned

- How to design a **recommendation algorithm from scratch** — without ML, without an API, just rules and data structures
- How to encode **domain knowledge** (color theory, fashion formality) into code
- The **dual-database adapter pattern** — same query interface for SQLite (fast local dev) and PostgreSQL (production), with a normalization layer for schema differences
- **TypeScript** discipline: the `WardrobeItem` and `OutfitResult` types caught several bugs during development that vanilla JS would have silently passed through
- How to build a **Vite + Express** monorepo where the build output is served by the API server — one `node server/index.js` command runs the full app

---

## Part of a Larger Portfolio

This app is part of a collection of self-built projects. See also:

- [FreightDesk Pro](../README.md) — full-stack billing & finance app for an Indian freight business
