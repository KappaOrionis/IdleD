-- IdleD Local Encyclopedia Database Schema
-- Multi-agent read-only reference data for game entities, spells, zaaps and routing.

CREATE TABLE IF NOT EXISTS spells (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    class_name TEXT NOT NULL,
    ap_cost INTEGER NOT NULL,
    min_range INTEGER NOT NULL,
    max_range INTEGER NOT NULL,
    requires_los BOOLEAN NOT NULL DEFAULT 1,
    description TEXT
);

CREATE TABLE IF NOT EXISTS monsters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    min_level INTEGER NOT NULL,
    max_level INTEGER NOT NULL,
    threat_rating INTEGER NOT NULL, -- 1 (Passif) à 5 (Extrêmement Dangereux)
    drops TEXT -- JSON format
);

CREATE TABLE IF NOT EXISTS transport_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    node_type TEXT NOT NULL, -- 'Zaap', 'Zaapi', 'Subway'
    pos_x INTEGER NOT NULL,
    pos_y INTEGER NOT NULL,
    subarea TEXT
);

CREATE TABLE IF NOT EXISTS map_tiles (
    tile_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pos_x INTEGER NOT NULL,
    pos_y INTEGER NOT NULL,
    subarea TEXT,
    has_resources BOOLEAN DEFAULT 0,
    has_monsters BOOLEAN DEFAULT 0
);
