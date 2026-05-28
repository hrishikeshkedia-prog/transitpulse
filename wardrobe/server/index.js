'use strict';
const express = require('express');
const path    = require('path');

const app  = express();
const PORT = process.env.PORT || 3800;

app.use(express.json());
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});

app.use('/uploads', express.static(path.join(__dirname, '..', 'uploads')));
app.use('/api/items',  require('./routes/items'));
app.use('/api/outfit', require('./routes/outfits'));

app.get('/api/health', (req, res) => res.json({ ok: true }));

const clientDist = path.join(__dirname, '..', 'client', 'dist');
app.use(express.static(clientDist));
app.get('*', (req, res) => {
  res.sendFile(path.join(clientDist, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Wardrobe server running at http://localhost:${PORT}`);
});
