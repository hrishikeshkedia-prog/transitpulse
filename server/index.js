'use strict';
const express = require('express');
const cors    = require('cors');
const jwt     = require('jsonwebtoken');
const bcrypt  = require('bcryptjs');
const fs      = require('fs');
const path    = require('path');

const PORT      = parseInt(process.env.PORT || '3742', 10);
const SECRET    = process.env.JWT_SECRET || 'fdp-change-me-in-production-use-a-long-random-string';
const DATA_DIR  = process.env.DATA_DIR || path.join(__dirname, 'data');
const VALID_TYPES = ['tr', 'py', 'iv', 'cl', 'co', 'fi', 'ml'];

// ── File-based store (no native deps) ────────────────────────────────────────
if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });

const USERS_FILE = path.join(DATA_DIR, '_users.json');

function readUsers() {
  try { return JSON.parse(fs.readFileSync(USERS_FILE, 'utf8')); } catch { return {}; }
}
function writeUsers(users) {
  fs.writeFileSync(USERS_FILE, JSON.stringify(users, null, 2));
}

function userDataFile(username) {
  return path.join(DATA_DIR, username.replace(/[^a-z0-9_-]/g, '_') + '.json');
}
function readUserData(username) {
  try { return JSON.parse(fs.readFileSync(userDataFile(username), 'utf8')); } catch { return {}; }
}
function writeUserData(username, data) {
  fs.writeFileSync(userDataFile(username), JSON.stringify(data, null, 2));
}

// ── Express ───────────────────────────────────────────────────────────────────
const app = express();
app.use(cors());
app.use(express.json({ limit: '10mb' }));

function requireAuth(req, res, next) {
  const h = req.headers.authorization || '';
  if (!h.startsWith('Bearer ')) return res.status(401).json({ error: 'Unauthorized' });
  try {
    req.user = jwt.verify(h.slice(7), SECRET);
    next();
  } catch {
    res.status(401).json({ error: 'Token invalid or expired' });
  }
}

function makeToken(username, name) {
  return jwt.sign({ username, name }, SECRET, { expiresIn: '30d' });
}

// ── Health ────────────────────────────────────────────────────────────────────
app.get('/api/health', (_, res) => res.json({ ok: true, version: '1.0.0' }));

// ── Auth ──────────────────────────────────────────────────────────────────────
app.post('/api/auth/check-username', (req, res) => {
  const { username } = req.body || {};
  if (!username) return res.status(400).json({ error: 'Missing username' });
  const users = readUsers();
  res.json({ available: !users[username.trim().toLowerCase()] });
});

app.post('/api/auth/register', (req, res) => {
  const { username, name, password } = req.body || {};
  if (!username || !name || !password) return res.status(400).json({ error: 'Missing fields' });
  const u = username.trim().toLowerCase();
  if (u.length < 3)        return res.status(400).json({ error: 'Username too short (min 3)' });
  if (password.length < 4) return res.status(400).json({ error: 'Password too short (min 4)' });
  const users = readUsers();
  if (users[u]) return res.status(409).json({ error: 'Username already taken' });
  users[u] = { name: name.trim(), hash: bcrypt.hashSync(password, 10) };
  writeUsers(users);
  res.json({ token: makeToken(u, name.trim()), username: u, name: name.trim() });
});

app.post('/api/auth/login', (req, res) => {
  const { username, password } = req.body || {};
  if (!username || !password) return res.status(400).json({ error: 'Missing fields' });
  const u     = username.trim().toLowerCase();
  const users = readUsers();
  const user  = users[u];
  if (!user || !bcrypt.compareSync(password, user.hash)) {
    return res.status(401).json({ error: 'Invalid username or password' });
  }
  res.json({ token: makeToken(u, user.name), username: u, name: user.name });
});

app.get('/api/auth/me', requireAuth, (req, res) => {
  const users = readUsers();
  const user  = users[req.user.username];
  if (!user) return res.status(404).json({ error: 'User not found' });
  res.json({ username: req.user.username, name: user.name });
});

// ── Data ──────────────────────────────────────────────────────────────────────
app.get('/api/data', requireAuth, (req, res) => {
  res.json(readUserData(req.user.username));
});

app.put('/api/data', requireAuth, (req, res) => {
  const current = readUserData(req.user.username);
  for (const type of VALID_TYPES) {
    if (type in req.body) current[type] = req.body[type];
  }
  writeUserData(req.user.username, current);
  res.json({ ok: true });
});

app.get('/api/data/:type', requireAuth, (req, res) => {
  if (!VALID_TYPES.includes(req.params.type)) return res.status(400).json({ error: 'Unknown type' });
  const data = readUserData(req.user.username);
  res.json(data[req.params.type] ?? null);
});

app.put('/api/data/:type', requireAuth, (req, res) => {
  if (!VALID_TYPES.includes(req.params.type)) return res.status(400).json({ error: 'Unknown type' });
  const data = readUserData(req.user.username);
  data[req.params.type] = req.body;
  writeUserData(req.user.username, data);
  res.json({ ok: true });
});

// ── Start ─────────────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`FreightDesk Pro server →  http://localhost:${PORT}`);
  console.log(`Data directory:           ${DATA_DIR}`);
  if (SECRET.startsWith('fdp-change-me')) {
    console.warn('⚠  WARNING: using default JWT_SECRET. Set JWT_SECRET env var before going to production.');
  }
});
