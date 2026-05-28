'use strict';
const path = require('path');

const USE_PG = !!process.env.DATABASE_URL;

let _pool = null;
let _sq   = null;

async function init() {
  if (USE_PG) {
    const { Pool } = require('pg');
    _pool = new Pool({
      connectionString: process.env.DATABASE_URL,
      ssl: { rejectUnauthorized: false },
    });
    await _pool.query(`
      CREATE TABLE IF NOT EXISTS items (
        id            TEXT PRIMARY KEY,
        name          TEXT NOT NULL,
        category      TEXT NOT NULL,
        color         TEXT NOT NULL,
        color_family  TEXT NOT NULL DEFAULT 'neutral',
        formality_min INTEGER NOT NULL DEFAULT 1,
        formality_max INTEGER NOT NULL DEFAULT 5,
        style_tags    JSONB NOT NULL DEFAULT '[]'::jsonb,
        image_data    TEXT,
        notes         TEXT NOT NULL DEFAULT '',
        created_at    BIGINT NOT NULL
      )
    `);
    console.log('PostgreSQL ready');
  } else {
    const Database = require('better-sqlite3');
    const DB_PATH = path.join(__dirname, '..', 'wardrobe.db');
    _sq = new Database(DB_PATH);
    _sq.pragma('journal_mode = WAL');
    _sq.exec(`
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
        notes         TEXT NOT NULL DEFAULT '',
        created_at    INTEGER NOT NULL
      )
    `);
    console.log('SQLite ready (local dev)');
  }
}

// Unified async query — returns array of rows
async function query(sql, params = []) {
  if (USE_PG) {
    const r = await _pool.query(sql, params);
    return r.rows;
  }
  // SQLite: convert $1 $2 → ? ?
  const sqSql = sql.replace(/\$\d+/g, '?');
  if (/^\s*(SELECT|WITH)/i.test(sql.trim())) {
    return _sq.prepare(sqSql).all(...params).map(normaliseRow);
  }
  _sq.prepare(sqSql).run(...params);
  return [];
}

async function queryOne(sql, params = []) {
  const rows = await query(sql, params);
  return rows[0] ?? null;
}

// SQLite rows have style_tags as a JSON string; normalise to array
function normaliseRow(row) {
  if (row && typeof row.style_tags === 'string') {
    return { ...row, style_tags: JSON.parse(row.style_tags) };
  }
  return row;
}

module.exports = { init, query, queryOne };
