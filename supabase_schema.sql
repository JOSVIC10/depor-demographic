-- ==============================================================================
-- DEPOR DEMOGRAPHIC & MATCH REPORT - SUPABASE DATABASE SCHEMA
-- Copia y pega este script en el SQL Editor de tu Dashboard de Supabase y pulsa "Run"
-- ==============================================================================

-- 1. Tablas principales
CREATE TABLE IF NOT EXISTS public.teams (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    season TEXT NOT NULL,
    club_name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.players (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    birthdate TEXT NOT NULL,
    detailed_position TEXT NOT NULL,
    derived_category TEXT NOT NULL,
    team_id TEXT REFERENCES public.teams(id) ON DELETE CASCADE,
    pitch_x REAL,
    pitch_y REAL,
    photo_url TEXT,
    minutes_played INTEGER DEFAULT 0,
    starts INTEGER DEFAULT 0,
    subs_in INTEGER DEFAULT 0,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    goals INTEGER DEFAULT 0,
    seasons_data TEXT,
    is_injured INTEGER DEFAULT 0,
    injury_description TEXT DEFAULT '',
    injury_return_time TEXT DEFAULT '',
    injury_phase TEXT DEFAULT '',
    extra_pitch_team_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.matches (
    id TEXT PRIMARY KEY,
    team_id TEXT REFERENCES public.teams(id) ON DELETE CASCADE,
    opponent TEXT NOT NULL,
    date TEXT NOT NULL,
    result_type TEXT NOT NULL,
    home_goals INTEGER NOT NULL,
    away_goals INTEGER NOT NULL,
    is_home INTEGER NOT NULL,
    competition TEXT NOT NULL,
    match_type TEXT DEFAULT 'LIGA',
    matchday TEXT DEFAULT '',
    custom_title TEXT,
    playing_time TEXT DEFAULT '90 Minutes',
    substitute_cadence TEXT DEFAULT '',
    substitution_times TEXT DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.lineup_entries (
    id TEXT PRIMARY KEY,
    match_id TEXT REFERENCES public.matches(id) ON DELETE CASCADE,
    player_id TEXT REFERENCES public.players(id) ON DELETE CASCADE,
    is_starter INTEGER NOT NULL,
    is_substitute INTEGER NOT NULL,
    grid_x REAL,
    grid_y REAL,
    position_label TEXT,
    minute_in INTEGER,
    minute_out INTEGER,
    minutes_played INTEGER DEFAULT 0,
    has_yellow_card INTEGER DEFAULT 0,
    has_red_card INTEGER DEFAULT 0,
    card_minute INTEGER,
    card_type TEXT,
    goals INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.substitutions (
    id TEXT PRIMARY KEY,
    match_id TEXT REFERENCES public.matches(id) ON DELETE CASCADE,
    player_out_id TEXT REFERENCES public.players(id) ON DELETE CASCADE,
    player_in_id TEXT REFERENCES public.players(id) ON DELETE CASCADE,
    minute INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Habilitar Políticas de Seguridad (RLS) y permitir lectura/escritura pública con la anon key
ALTER TABLE public.teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.players ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lineup_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.substitutions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Public full access teams" ON public.teams;
CREATE POLICY "Public full access teams" ON public.teams FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Public full access players" ON public.players;
CREATE POLICY "Public full access players" ON public.players FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Public full access matches" ON public.matches;
CREATE POLICY "Public full access matches" ON public.matches FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Public full access lineup_entries" ON public.lineup_entries;
CREATE POLICY "Public full access lineup_entries" ON public.lineup_entries FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Public full access substitutions" ON public.substitutions;
CREATE POLICY "Public full access substitutions" ON public.substitutions FOR ALL USING (true) WITH CHECK (true);
