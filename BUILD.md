# FreightDesk Pro — Electron Desktop App

A cross-platform desktop app for transport billing, CFA invoicing, finance, and Tally export.  
Runs on **Windows, macOS, and Linux** with zero internet required after install.

---

## Quick start (dev / preview)

```bash
npm install
npm start
```

This opens the app in a native window. All data is stored locally using `localStorage`.

---

## Build installers

> Requires Node.js 18+ and npm.

### Windows (produces `.exe` installer + portable `.exe`)
```bash
npm run build:win
```

### macOS (produces `.dmg`)
```bash
npm run build:mac
```

### Linux (produces `.AppImage` + `.deb`)
```bash
npm run build:linux
```

### All platforms at once
```bash
npm run build:all
```

Outputs land in `dist/`.

---

## What's bundled

| File | Purpose |
|------|---------|
| `index.html` | The entire app (single self-contained file) |
| `main.js` | Electron main process |
| `preload.js` | Security bridge (context isolation) |
| `assets/chart.umd.js` | Chart.js — bundled for offline use |
| `assets/icon.png` | App icon (512×512) |

Fonts (Inter, JetBrains Mono) load from Google Fonts when online; system sans-serif is used as offline fallback.

---

## Data & backup

All data lives in Electron's `localStorage` (per-user, per-machine).  
Use **Settings → Export Backup** regularly to save a `.json` snapshot.  
Use **Settings → Import Backup** to restore on a new machine.
