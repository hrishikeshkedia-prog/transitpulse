'use strict';
const Database = require('better-sqlite3');
const path = require('path');

const DB_PATH = process.env.DB_PATH || path.join(__dirname, '..', 'wardrobe.db');
const db = new Database(DB_PATH);

db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');

db.exec(`
  CREATE TABLE IF NOT EXISTS items (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    category      TEXT NOT NULL,
    color         TEXT NOT NULL,
    color_family  TEXT NOT NULL DEFAULT 'neutral',
    formality_min INTEGER NOT NULL DEFAULT 1,
    formality_max INTEGER NOT NULL DEFAULT 5,
    style_tags    TEXT NOT NULL DEFAULT '[]',
    image_data    TEXT,
    notes         TEXT DEFAULT '',
    created_at    INTEGER NOT NULL
  );
`);

module.exports = db;
