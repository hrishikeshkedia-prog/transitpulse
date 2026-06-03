# FreightDesk Pro

> A full-stack Progressive Web App that replaced pen-and-paper billing for a real freight forwarding business — built entirely by a high school student.

---

## The Problem I Solved

Indian freight and logistics businesses — especially small CFA (Clearing & Forwarding Agents) and transport operators — still run their billing on paper registers or fragile Excel sheets. When I looked at how my family's freight business tracked transport invoices, CFA bills, client payments, and Tally exports, I saw a workflow that hadn't changed in decades.

I built FreightDesk Pro to fix that. It's a mobile-first billing and finance management system, designed specifically for how Indian freight businesses actually work: Indian number formatting (₹1,23,456), Tally accounting integration, GST-ready invoices, and an offline-first architecture so it works even on patchy mobile internet.

---

## What It Does

| Module | What it handles |
|---|---|
| **Transport Invoices** | Generate print-ready A4 transport billing invoices with LR numbers, PO dates, GST rows, and Indian currency formatting |
| **CFA Bills** | Issue CFA invoices with itemised rates, auto-incrementing bill numbers shared across both invoice types |
| **Finance Tracker** | Track client payments, EMI schedules with progress bars, and monthly revenue breakdowns via Chart.js |
| **Tally Export** | Export all financial data in a format compatible with Tally ERP — the standard accounting software for Indian SMBs |
| **Email Templates** | Save and manage email templates for recurring client communication |
| **Cloud Sync** | Optional self-hosted sync server so the business owner's data is backed up and accessible across devices |
| **PWA / Offline** | Installable as a home screen app; works fully offline via Service Worker caching |

---

## Technical Stack

```
Frontend      Vanilla JS, CSS custom properties, Chart.js
Backend       Node.js + Express.js
Database      PostgreSQL (production) / JSON file store (development)
Auth          JWT (HS256, hand-rolled implementation)
Hosting       GitHub Pages (frontend) + self-hosted VPS (sync server)
PWA           Service Worker, Web App Manifest, install prompt
```

No framework dependencies on the frontend — just clean, hand-written HTML/CSS/JS. I chose this deliberately to understand the browser platform deeply rather than hiding behind abstractions.

---

## Architecture

```
┌─────────────────────────────────┐
│         Browser (PWA)           │
│   index.html  ←→  sync.js       │
│   Service Worker (sw.js)        │
│   localStorage (offline store)  │
└────────────┬────────────────────┘
             │ REST (JWT auth)
             ▼
┌─────────────────────────────────┐
│     Sync Server (Node.js)       │
│   /api/auth  /api/data          │
│   PostgreSQL or JSON files      │
└─────────────────────────────────┘
```

The app works 100% offline from localStorage. The sync server is optional — if no server URL is configured, the app stores everything locally. When a server is configured, it pushes/pulls a snapshot of all data on login and on every save, with conflict resolution logic to prevent newer local data from being overwritten by stale server data.

---

## Features Built for India

- **Indian number formatting** — amounts display as ₹1,23,456.00, not ₹123,456.00
- **Tally ERP compatibility** — export structure matches Tally's ledger/voucher format
- **GST invoice rows** — CGST/SGST/IGST rows with correct colspan layout
- **CFA billing** — industry-specific invoice type used by Clearing & Forwarding Agents
- **Multi-location support** — manage billing across different depot locations

---

## Key Engineering Challenges

**Offline-first sync without conflicts**
The hardest part was designing the sync layer. If a user edits data offline and then syncs, the server might have older data. I wrote a merge policy where non-empty local data never gets overwritten by empty server arrays — preventing data loss on fresh server deployments.

**Print-accurate A4 invoices**
Getting the invoice to fill an A4 page perfectly — both on screen and in print — required combining `@media print` CSS with `height: 100%` chains through the DOM. Fixed `mm` values broke on different printers; dynamic percentage fills worked correctly.

**JWT from scratch**
I implemented JWT auth without a library to understand how it works: base64url encoding, HMAC-SHA256 signing, and token verification. The production version uses a proper secret rotation strategy.

---

## Running Locally

**Frontend only (no server needed):**
```bash
# Serve with any static file server
npx serve .
# Then open http://localhost:3000
```

**With sync server:**
```bash
cd server
npm install
JWT_SECRET=your-secret node index.js
# Server runs on port 3742
```

**With PostgreSQL:**
```bash
DATABASE_URL=postgres://user:pass@localhost/freightdesk node index.js
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Server health check |
| `POST` | `/api/auth/register` | Create account |
| `POST` | `/api/auth/login` | Login, returns JWT |
| `GET` | `/api/auth/me` | Current user (auth required) |
| `GET` | `/api/data` | Fetch all user data |
| `PUT` | `/api/data` | Save all user data |

---

## Project Status

This app is actively used by the business it was built for. It has gone through multiple rounds of real-world feedback:

- Redesigned the invoice layout after print testing on an actual laser printer
- Fixed Indian comma formatting after the accountant flagged Western-style numbers
- Added the Tally export after realizing the CA needed data in that format
- Rewrote the sync merge logic after a sync event wiped a week of entries

---

## What I Learned

- How browsers work at the platform level: Service Workers, the Cache API, `localStorage`, `fetch`
- How to design for real users, not just demo scenarios — real data has edge cases
- How JWT authentication works end-to-end, from token generation to expiry handling
- Why Indian number systems differ from Western ones, and how to implement custom `Intl`-style formatting
- How to ship software that people actually depend on, and what it feels like when it breaks

---

## About

Built by Hrishikesh Kedia — a high school student passionate about building software that solves real problems for the people around him.

This project is part of a portfolio of self-built applications. See also: [Wardrobe App](#) *(coming soon)*
