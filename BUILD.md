# FreightDesk Pro — Electron Desktop App + Cloud Sync Server

A cross-platform desktop app for transport billing, CFA invoicing, finance, and Tally export.  
Runs on **Windows, macOS, and Linux** with zero internet required.  
Optionally connects to a **self-hosted sync server** for multi-device / multi-user access.

---

## Quick start (Electron desktop app)

```bash
npm install
npm start          # opens the app in a native window
```

Works fully offline — all data stored in localStorage.

---

## Cloud sync server

The sync server lets multiple users/devices share data. It requires **Node.js 18+** and nothing else (no database to install).

### Run locally

```bash
cd server
npm install
npm start
# → http://localhost:3742
```

### Run in production (any Linux server / VPS)

```bash
cd server
npm install
PORT=3742 JWT_SECRET=your-long-random-secret npm start
```

Or with `pm2` for auto-restart:

```bash
npm install -g pm2
PORT=3742 JWT_SECRET=your-secret pm2 start index.js --name freightdesk-server
pm2 save && pm2 startup
```

### Connect the desktop app to the server

1. Open the app → **Settings**
2. Find the **☁ Server Sync** card at the top
3. Enter your server URL (`http://your-server-ip:3742` or `https://your-domain.com`)
4. Click **Connect**, then **Sign in** with your FreightDesk Pro credentials

From that point on, every save is pushed to the server and every load pulls from it. Local storage acts as an offline cache.

### Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `PORT` | `3742` | TCP port the server listens on |
| `JWT_SECRET` | *(insecure default)* | Secret used to sign JWTs — **change in production** |
| `DATA_DIR` | `server/data/` | Directory where user JSON files are stored |

---

## Build desktop installers

> Requires Node.js 18+ and npm.

```bash
npm run build:win     # → dist/*.exe  (Windows installer + portable)
npm run build:mac     # → dist/*.dmg  (macOS)
npm run build:linux   # → dist/*.AppImage + *.deb  (Linux)
npm run build:all     # all three platforms
```

Outputs land in `dist/`.

---

## Project layout

| File / Dir | Purpose |
|------------|---------|
| `index.html` | The full FreightDesk Pro app |
| `sync.js` | Cloud sync layer — patches save/load/auth to use the server |
| `main.js` | Electron main process |
| `preload.js` | Security bridge (context isolation) |
| `assets/chart.umd.js` | Chart.js bundled for offline use |
| `assets/icon.png` | App icon (512×512) |
| `server/` | Standalone Express sync server |
| `server/data/` | Per-user JSON data files (auto-created) |

---

## Data & backup

- **Local mode**: data lives in Electron's `localStorage` — use **Settings → Export Backup** regularly.
- **Server mode**: data is also persisted on the server in `server/data/<username>.json` — back up that directory.
- Import/Export still works in both modes — useful for migrating between devices or from local to server mode.
