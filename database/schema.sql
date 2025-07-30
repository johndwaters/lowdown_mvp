-- schema.sql
--
-- This script defines the database schema for The Lowdown newsletter app.
-- It includes tables for Articles, Threats, and Podcast Episodes.

-- Turn on foreign key support
PRAGMA foreign_keys = ON;

--------------------------------------------------------------------------------
-- 1. Articles Table
-- Stores collected articles, their summaries, and metadata.
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    title TEXT,
    source TEXT DEFAULT 'Manual',
    original_content TEXT,
    summary TEXT,
    status TEXT NOT NULL DEFAULT 'pending', -- e.g., pending, summarized, accepted, archived
    position INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

--------------------------------------------------------------------------------
-- 2. Threats Table
-- A versatile table for the 'Threat of the Day' feature.
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Threats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT, -- e.g., Aircraft, Missile, SAM
    country_of_origin TEXT,
    description TEXT,
    -- Flexible field for specs like speed, range, etc.
    specifications TEXT, -- Stored as JSON
    ioc_year INTEGER,
    -- Flexible field for a list of proliferated nations
    operators TEXT, -- Stored as JSON array
    image_url TEXT,
    tod_summary TEXT,
    status TEXT NOT NULL DEFAULT 'draft', -- e.g., draft, recommended, published
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

--------------------------------------------------------------------------------
-- 3. Snapshots Table
-- Stores snapshot articles with 1-sentence highlights for quick scanning.
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    title TEXT,
    source TEXT DEFAULT 'Manual',
    original_content TEXT,
    highlight TEXT, -- 1-sentence AI-generated highlight
    status TEXT NOT NULL DEFAULT 'pending', -- e.g., pending, highlighted, accepted, archived
    position INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

--------------------------------------------------------------------------------
-- 4. PodcastEpisodes Table
-- Stores metadata for podcast episodes.
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS PodcastEpisodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    episode_number INTEGER,
    podcast_url TEXT UNIQUE,
    description TEXT,
    published_date DATE,
    image_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Triggers to automatically update the 'updated_at' timestamp on changes

CREATE TRIGGER IF NOT EXISTS update_articles_updated_at
AFTER UPDATE ON Articles
FOR EACH ROW
BEGIN
    UPDATE Articles SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS update_threats_updated_at
AFTER UPDATE ON Threats
FOR EACH ROW
BEGIN
    UPDATE Threats SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS update_podcast_episodes_updated_at
AFTER UPDATE ON PodcastEpisodes
FOR EACH ROW
BEGIN
    UPDATE PodcastEpisodes SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;
