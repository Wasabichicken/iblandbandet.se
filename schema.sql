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
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    -- "Artistnamn" in the UI - an optional, self-chosen nickname/stage name,
    -- not a real-name field. The registry stays anonymous by default (see
    -- the "Members registry" note on this): nothing here requires a member
    -- to set one, and a member who doesn't is exactly as anonymous to
    -- others as before. Setting one is a deliberate choice to be more
    -- identifiable - e.g. so the chat feature can show it next to a
    -- message - not an expectation.
    name TEXT
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

-- API-only (see CHAT.md) - never rendered on the website. member_id uses
-- ON DELETE SET NULL, same precedent as events.created_by and
-- drive_items.owner_id: a member's messages survive their account being
-- deleted rather than vanishing or blocking the deletion. body and
-- image_uuid are both nullable since either can carry a message on its
-- own (a caption-less image, or a plain text message) - the CHECK just
-- rules out a message that's neither, mirroring drive_items' own
-- directory/file CHECK.
CREATE TABLE iblandbandet_chat_messages (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES iblandbandet_members(id) ON DELETE SET NULL,
    body TEXT,
    image_uuid UUID,
    image_size_bytes INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Client-generated (a UUID the client picks itself, not server-assigned)
    -- idempotency key for a send: a client that retries after a dropped
    -- connection/timeout can resend the identical request_id, and the
    -- UNIQUE constraint lets the server recognize the retry and hand back
    -- the original message rather than creating a real duplicate. Nullable
    -- since it's optional - a client that doesn't care about retry-safety
    -- doesn't need to supply one.
    request_id UUID UNIQUE,
    CHECK (body IS NOT NULL OR image_uuid IS NOT NULL)
);

-- Deliberately the same shape as iblandbandet_sessions (opaque token,
-- only its hash stored) but a separate table, not a shared one - the two
-- represent genuinely different clients with different lifetimes. Unlike
-- sessions, there's no expires_at: a native app shouldn't be forced to
-- re-authenticate on a schedule the way a browser session is, so a token
-- stays valid until the member explicitly logs out (DELETE via
-- dal/api_tokens.py's delete_api_token), not until a timer runs out.
CREATE TABLE iblandbandet_api_tokens (
    token_hash TEXT PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES iblandbandet_members(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
