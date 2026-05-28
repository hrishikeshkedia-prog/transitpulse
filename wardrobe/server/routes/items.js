'use strict';
const express = require('express');
const { v4: uuidv4 } = require('uuid');
const db = require('../db');

const router = express.Router();

router.get('/', (req, res) => {
  const { category } = req.query;
  let rows;
  if (category && category !== 'all') {
    rows = db.prepare('SELECT * FROM items WHERE category = ? ORDER BY created_at DESC').all(category);
  } else {
    rows = db.prepare('SELECT * FROM items ORDER BY created_at DESC').all();
  }
  res.json(rows.map(parseItem));
});

router.get('/:id', (req, res) => {
  const row = db.prepare('SELECT * FROM items WHERE id = ?').get(req.params.id);
  if (!row) return res.status(404).json({ error: 'Not found' });
  res.json(parseItem(row));
});

router.post('/', (req, res) => {
  const { name, category, color, color_family, formality_min, formality_max, style_tags, notes, image_data } = req.body ?? {};
  if (!name || !category || !color) {
    return res.status(400).json({ error: 'name, category, and color are required' });
  }
  const id = uuidv4();
  db.prepare(`
    INSERT INTO items (id, name, category, color, color_family, formality_min, formality_max, style_tags, image_data, notes, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).run(
    id, name, category, color,
    color_family || 'neutral',
    parseInt(formality_min) || 1,
    parseInt(formality_max) || 5,
    Array.isArray(style_tags) ? JSON.stringify(style_tags) : (style_tags || '[]'),
    image_data || null,
    notes || '',
    Date.now()
  );
  res.status(201).json(parseItem(db.prepare('SELECT * FROM items WHERE id = ?').get(id)));
});

router.put('/:id', (req, res) => {
  const existing = db.prepare('SELECT * FROM items WHERE id = ?').get(req.params.id);
  if (!existing) return res.status(404).json({ error: 'Not found' });
  const { name, category, color, color_family, formality_min, formality_max, style_tags, notes, image_data } = req.body ?? {};
  db.prepare(`
    UPDATE items SET name=?, category=?, color=?, color_family=?, formality_min=?, formality_max=?, style_tags=?, image_data=?, notes=?
    WHERE id=?
  `).run(
    name || existing.name,
    category || existing.category,
    color || existing.color,
    color_family || existing.color_family,
    parseInt(formality_min) || existing.formality_min,
    parseInt(formality_max) || existing.formality_max,
    Array.isArray(style_tags) ? JSON.stringify(style_tags) : (style_tags || existing.style_tags),
    image_data !== undefined ? (image_data || null) : existing.image_data,
    notes !== undefined ? notes : existing.notes,
    req.params.id
  );
  res.json(parseItem(db.prepare('SELECT * FROM items WHERE id = ?').get(req.params.id)));
});

router.delete('/:id', (req, res) => {
  if (!db.prepare('SELECT id FROM items WHERE id = ?').get(req.params.id)) {
    return res.status(404).json({ error: 'Not found' });
  }
  db.prepare('DELETE FROM items WHERE id = ?').run(req.params.id);
  res.json({ ok: true });
});

function parseItem(row) {
  return { ...row, style_tags: JSON.parse(row.style_tags || '[]') };
}

module.exports = router;
