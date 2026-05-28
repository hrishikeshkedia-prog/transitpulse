'use strict';
const express = require('express');
const db      = require('../db');
const { recommend } = require('../outfit-engine');

const router = express.Router();

router.post('/recommend', (req, res) => {
  const { formalityLevel, description } = req.body;
  const level = parseInt(formalityLevel);
  if (!level || level < 1 || level > 5) {
    return res.status(400).json({ error: 'formalityLevel must be 1-5' });
  }

  const items = db.prepare('SELECT * FROM items').all().map(row => ({
    ...row, style_tags: JSON.parse(row.style_tags || '[]'),
  }));

  if (!items.length) {
    return res.status(422).json({ error: 'No items in your wardrobe yet' });
  }

  const result = recommend(items, level, description || '');
  if (!result) {
    return res.status(422).json({ error: 'Not enough compatible items for this formality level' });
  }

  res.json(result);
});

module.exports = router;
