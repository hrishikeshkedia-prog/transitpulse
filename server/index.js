'use strict';
const express = require('express');
const fs      = require('fs');
const path    = require('path');
const crypto  = require('crypto');

const app        = express();
const PORT       = process.env.PORT       || 3742;
const JWT_SECRET = process.env.JWT_SECRET || 'change-me-in-production';
const DATA_DIR   = process.env.DATA_DIR   || path.join(__dirname, 'data');
const VERSION    = '1.0.0';

fs.mkdirSync(DATA_DIR, { recursive: true });

app.use(express.json());
app.use(function (req, res, next) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,PUT,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type,Authorization');
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});

function readJSON(file)       { try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return null; } }
function writeJSON(file, data){ fs.writeFileSync(file, JSON.stringify(data, null, 2)); }
function usersFile()          { return path.join(DATA_DIR, '_users.json'); }
function dataFile(u)          { return path.join(DATA_DIR, u + '.json'); }
function getUsers()           { return readJSON(usersFile()) || {}; }
function saveUsers(u)         { writeJSON(usersFile(), u); }

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

app.get('/api/health', function (req, res) { res.json({ ok: true, version: VERSION }); });

app.post('/api/auth/register', function (req, res) {
  const { username, name, password } = req.body || {};
  if (!username || !password) return res.status(400).json({ error: 'Username and password required' });
  const users = getUsers();
  if (users[username]) return res.status(409).json({ error: 'Username already taken' });
  users[username] = { name: name || username, hash: hashPassword(password), createdAt: Date.now() };
  saveUsers(users);
  res.json({ token: makeToken(username, users[username].name), username, name: users[username].name });
});

app.post('/api/auth/login', function (req, res) {
  const { username, password } = req.body || {};
  const users = getUsers();
  const user  = users[username];
  if (!user || !checkPassword(password, user.hash))
    return res.status(401).json({ error: 'Invalid username or password' });
  res.json({ token: makeToken(username, user.name), username, name: user.name });
});

app.get('/api/auth/me', auth, function (req, res) {
  const user = (getUsers()[req.username]) || {};
  res.json({ username: req.username, name: user.name });
});

app.get('/api/data', auth, function (req, res) { res.json(readJSON(dataFile(req.username)) || {}); });
app.put('/api/data', auth, function (req, res) { writeJSON(dataFile(req.username), req.body); res.json({ ok: true }); });

app.listen(PORT, function () {
  console.log('FreightDesk Pro sync server on port ' + PORT);
});
