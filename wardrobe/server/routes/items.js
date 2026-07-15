'use strict';
const express = require('express');
const { v4: uuidv4 } = require('uuid');
const { query, queryOne } = require('../db');

const router = express.Router();

router.get('/', async (req, res) => {
  try {
    const { category } = req.query;
    const rows = category && category !== 'all'
      ? await query('SELECT * FROM items WHERE category = $1 ORDER BY created_at DESC', [category])
      : await query('SELECT * FROM items ORDER BY created_at DESC');
    res.json(rows);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

router.get('/:id', async (req, res) => {
  try {
    const row = await queryOne('SELECT * FROM items WHERE id = $1', [req.params.id]);
    if (!row) return res.status(404).json({ error: 'Not found' });
    res.json(row);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

router.post('/', async (req, res) => {
  try {
    const { name, category, color, color_family, formality_min, formality_max, style_tags, notes, image_data } = req.body ?? {};
    if (!name || !category || !color) return res.status(400).json({ error: 'name, category, and color are required' });
    const id = uuidv4();
    const tags = Array.isArray(style_tags) ? JSON.stringify(style_tags) : (style_tags || '[]');
    await query(
      `INSERT INTO items (id,name,category,color,color_family,formality_min,formality_max,style_tags,image_data,notes,created_at)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8::jsonb,$9,$10,$11)`,
      [id, name, category, color, color_family || 'neutral',
       parseInt(formality_min) || 1, parseInt(formality_max) || 5,
       tags, image_data || null, notes || '', Date.now()]
    );
    const row = await queryOne('SELECT * FROM items WHERE id = $1', [id]);
    res.status(201).json(row);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

router.put('/:id', async (req, res) => {
  try {
    const existing = await queryOne('SELECT * FROM items WHERE id = $1', [req.params.id]);
    if (!existing) return res.status(404).json({ error: 'Not found' });
    const { name, category, color, color_family, formality_min, formality_max, style_tags, notes, image_data } = req.body ?? {};
    const tags = Array.isArray(style_tags) ? JSON.stringify(style_tags)
      : (style_tags ?? JSON.stringify(existing.style_tags));
    await query(
      `UPDATE items SET name=$1,category=$2,color=$3,color_family=$4,formality_min=$5,formality_max=$6,style_tags=$7::jsonb,image_data=$8,notes=$9
       WHERE id=$10`,
      [name || existing.name, category || existing.category, color || existing.color,
       color_family || existing.color_family,
       parseInt(formality_min) || existing.formality_min,
       parseInt(formality_max) || existing.formality_max,
       tags, image_data !== undefined ? (image_data || null) : existing.image_data,
       notes !== undefined ? notes : existing.notes, req.params.id]
    );
    const row = await queryOne('SELECT * FROM items WHERE id = $1', [req.params.id]);
    res.json(row);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

router.delete('/:id', async (req, res) => {
  try {
    const existing = await queryOne('SELECT id FROM items WHERE id = $1', [req.params.id]);
    if (!existing) return res.status(404).json({ error: 'Not found' });
    await query('DELETE FROM items WHERE id = $1', [req.params.id]);
    res.json({ ok: true });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

module.exports = router;
