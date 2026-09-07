CREATE TABLE iblandbandet_members (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    password_iterations INTEGER NOT NULL,
    instruments TEXT,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    profile_picture TEXT,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE iblandbandet_sessions (
    token_hash TEXT PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES iblandbandet_members(id) ON DELETE CASCADE,
    csrf_token TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE iblandbandet_password_resets (
    token_hash TEXT PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES iblandbandet_members(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ
);

CREATE TABLE iblandbandet_subtitles (
    id SERIAL PRIMARY KEY,
    subtitle TEXT NOT NULL
);

CREATE TABLE iblandbandet_events (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ,
    location TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    description TEXT,
    created_by INTEGER REFERENCES iblandbandet_members(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
