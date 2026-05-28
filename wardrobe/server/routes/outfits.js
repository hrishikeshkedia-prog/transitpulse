'use strict';
const express = require('express');
const { query } = require('../db');
const { recommend } = require('../outfit-engine');

const router = express.Router();

router.post('/recommend', async (req, res) => {
  try {
    const { formalityLevel, description } = req.body;
    const level = parseInt(formalityLevel);
    if (!level || level < 1 || level > 5) {
      return res.status(400).json({ error: 'formalityLevel must be 1–5' });
    }

    const items = await query('SELECT * FROM items');
    if (!items.length) {
      return res.status(422).json({ error: 'No items in your wardrobe yet' });
    }

    const result = recommend(items, level, description || '');
    if (!result) {
      return res.status(422).json({ error: 'Not enough compatible items for this formality level' });
    }
    res.json(result);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

module.exports = router;
