'use strict';
const express = require('express');
const multer  = require('multer');
const path    = require('path');
const { v4: uuidv4 } = require('uuid');
const db      = require('../db');

const router = express.Router();

const storage = multer.diskStorage({
  destination: path.join(__dirname, '../../uploads'),
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname) || '.jpg';
    cb(null, uuidv4() + ext);
  },
});
const upload = multer({
  storage,
  limits: { fileSize: 10 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('image/')) cb(null, true);
    else cb(new Error('Only image files allowed'));
  },
});

router.get('/', (req, res) => {
  const category = req.query.category;
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

router.post('/', upload.single('image'), (req, res) => {
  const { name, category, color, color_family, formality_min, formality_max, style_tags, notes } = req.body;
  if (!name || !category || !color) {
    return res.status(400).json({ error: 'name, category, and color are required' });
  }
  const id = uuidv4();
  const image_path = req.file ? req.file.filename : null;
  db.prepare(`
    INSERT INTO items (id, name, category, color, color_family, formality_min, formality_max, style_tags, image_path, notes, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).run(
    id, name, category, color,
    color_family || 'neutral',
    parseInt(formality_min) || 1,
    parseInt(formality_max) || 5,
    style_tags || '[]',
    image_path,
    notes || '',
    Date.now()
  );
  const row = db.prepare('SELECT * FROM items WHERE id = ?').get(id);
  res.status(201).json(parseItem(row));
});

router.put('/:id', upload.single('image'), (req, res) => {
  const existing = db.prepare('SELECT * FROM items WHERE id = ?').get(req.params.id);
  if (!existing) return res.status(404).json({ error: 'Not found' });

  const { name, category, color, color_family, formality_min, formality_max, style_tags, notes } = req.body;
  const image_path = req.file ? req.file.filename : existing.image_path;

  db.prepare(`
    UPDATE items SET name=?, category=?, color=?, color_family=?, formality_min=?, formality_max=?, style_tags=?, image_path=?, notes=?
    WHERE id=?
  `).run(
    name || existing.name,
    category || existing.category,
    color || existing.color,
    color_family || existing.color_family,
    parseInt(formality_min) || existing.formality_min,
    parseInt(formality_max) || existing.formality_max,
    style_tags || existing.style_tags,
    image_path,
    notes !== undefined ? notes : existing.notes,
    req.params.id
  );
  const row = db.prepare('SELECT * FROM items WHERE id = ?').get(req.params.id);
  res.json(parseItem(row));
});

router.delete('/:id', (req, res) => {
  const existing = db.prepare('SELECT * FROM items WHERE id = ?').get(req.params.id);
  if (!existing) return res.status(404).json({ error: 'Not found' });
  db.prepare('DELETE FROM items WHERE id = ?').run(req.params.id);
  res.json({ ok: true });
});

function parseItem(row) {
  return { ...row, style_tags: JSON.parse(row.style_tags || '[]') };
}

module.exports = router;
