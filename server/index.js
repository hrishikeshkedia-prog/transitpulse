'use strict';
const express = require('express');
const fs      = require('fs');
const path    = require('path');
const crypto  = require('crypto');

const app        = express();
const PORT       = process.env.PORT       || 3742;
const JWT_SECRET = process.env.JWT_SECRET || 'change-me-in-production';
const DATA_DIR   = process.env.DATA_DIR   || path.join(__dirname, 'data');
const VERSION    = '1.1.0';

// ── Storage: PostgreSQL if DATABASE_URL is set, otherwise local files ─────────
let pool = null;
if (process.env.DATABASE_URL) {
  const { Pool } = require('pg');
  pool = new Pool({ connectionString: process.env.DATABASE_URL, ssl: { rejectUnauthorized: false } });
  pool.query('CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
    .then(() => console.log('PostgreSQL storage ready'))
    .catch(e => { console.error('DB init error:', e.message); pool = null; });
} else {
  fs.mkdirSync(DATA_DIR, { recursive: true });
  console.log('File storage ready (data will not persist across restarts)');
}

async function kvGet(key) {
  if (pool) {
    const r = await pool.query('SELECT value FROM kv WHERE key=$1', [key]);
    return r.rows[0] ? JSON.parse(r.rows[0].value) : null;
  }
  try { return JSON.parse(fs.readFileSync(path.join(DATA_DIR, key + '.json'), 'utf8')); } catch { return null; }
}

async function kvSet(key, value) {
  if (pool) {
    await pool.query(
      'INSERT INTO kv(key,value) VALUES($1,$2) ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value',
      [key, JSON.stringify(value)]
    );
    return;
  }
  fs.writeFileSync(path.join(DATA_DIR, key + '.json'), JSON.stringify(value, null, 2));
}
// ─────────────────────────────────────────────────────────────────────────────

app.use(express.json({ limit: '10mb' }));
app.use(function (req, res, next) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,PUT,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type,Authorization');
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});

function b64url(buf) { return buf.toString('base64').replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,''); }
function signJWT(payload) {
  const h = b64url(Buffer.from(JSON.stringify({ alg:'HS256', typ:'JWT' })));
  const b = b64url(Buffer.from(JSON.stringify(payload)));
  const s = b64url(crypto.createHmac('sha256', JWT_SECRET).update(h+'.'+b).digest());
  return h+'.'+b+'.'+s;
}
function verifyJWT(token) {
  try {
    const [h, b, s] = token.split('.');
    const expected  = b64url(crypto.createHmac('sha256', JWT_SECRET).update(h+'.'+b).digest());
    if (s !== expected) return null;
    const p = JSON.parse(Buffer.from(b, 'base64').toString());
    if (p.exp && Date.now()/1000 > p.exp) return null;
    return p;
  } catch { return null; }
}
function hashPassword(pw) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.createHmac('sha256', salt).update(pw).digest('hex');
  return salt + ':' + hash;
}
function checkPassword(pw, stored) {
  const [salt, hash] = stored.split(':');
  return crypto.createHmac('sha256', salt).update(pw).digest('hex') === hash;
}
function auth(req, res, next) {
  const tok = (req.headers['authorization'] || '').replace('Bearer ', '');
  const p   = verifyJWT(tok);
  if (!p) return res.status(401).json({ error: 'Unauthorized' });
  req.username = p.sub;
  next();
}
function makeToken(username, name) {
  return signJWT({ sub: username, name, iat: Math.floor(Date.now()/1000), exp: Math.floor(Date.now()/1000) + 86400*30 });
}

app.get('/api/health', function (req, res) {
  res.json({ ok: true, version: VERSION, storage: pool ? 'postgres' : 'file' });
});

app.post('/api/auth/register', async function (req, res) {
  try {
    const { username, name, password } = req.body || {};
    if (!username || !password) return res.status(400).json({ error: 'Username and password required' });
    const users = await kvGet('_users') || {};
    if (users[username]) return res.status(409).json({ error: 'Username already taken' });
    users[username] = { name: name || username, hash: hashPassword(password), createdAt: Date.now() };
    await kvSet('_users', users);
    res.json({ token: makeToken(username, users[username].name), username, name: users[username].name });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.post('/api/auth/login', async function (req, res) {
  try {
    const { username, password } = req.body || {};
    const users = await kvGet('_users') || {};
    const user  = users[username];
    if (!user || !checkPassword(password, user.hash))
      return res.status(401).json({ error: 'Invalid username or password' });
    res.json({ token: makeToken(username, user.name), username, name: user.name });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.get('/api/auth/me', auth, async function (req, res) {
  try {
    const users = await kvGet('_users') || {};
    const user  = users[req.username] || {};
    res.json({ username: req.username, name: user.name });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.get('/api/data', auth, async function (req, res) {
  try { res.json(await kvGet('data_' + req.username) || {}); }
  catch (e) { res.status(500).json({ error: e.message }); }
});

app.put('/api/data', auth, async function (req, res) {
  try { await kvSet('data_' + req.username, req.body); res.json({ ok: true }); }
  catch (e) { res.status(500).json({ error: e.message }); }
});

app.use(express.static(path.join(__dirname, '..')));

app.listen(PORT, function () {
  console.log('FreightDesk Pro sync server v' + VERSION + ' on port ' + PORT);
});
