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

-- parent_id has no ON DELETE clause (defaults to RESTRICT) - the database
-- itself refuses to delete a directory row that still has children,
-- matching the app-level "directories must be empty before deletion" rule
-- with a hard backstop. owner_id uses ON DELETE SET NULL (same pattern as
-- events.created_by) so a member's files/folders survive their account
-- being deleted, becoming permanently undeletable via the normal
-- owner-only-delete path once orphaned - an accepted consequence, not a bug.
CREATE TABLE iblandbandet_drive_items (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER REFERENCES iblandbandet_drive_items(id),
    owner_id INTEGER REFERENCES iblandbandet_members(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    is_directory BOOLEAN NOT NULL,
    storage_uuid UUID,
    size_bytes INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (
        (is_directory AND storage_uuid IS NULL AND size_bytes IS NULL)
        OR
        (NOT is_directory AND storage_uuid IS NOT NULL AND size_bytes IS NOT NULL)
    )
);
