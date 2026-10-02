// The chat relay Durable Object: bridges connected WebSocket clients to
// accum.se, which stays the single source of truth for every message (see
// CHAT.md). Persist-then-broadcast: a client's "message"/"delete" sent over
// the socket is first persisted via a normal call back to accum.se's
// existing bearer-token-authenticated api/chat.cgi (the same endpoint a
// plain REST client would use) - only once that succeeds does the confirmed
// result get broadcast to every connected client, sender included. If the
// persist call fails, nothing is broadcast; the sender alone gets a
// {"type": "error"}.
//
// Image messages take the opposite path (see CHAT.md's "Image attachments"):
// accum.se persists them directly via its own multipart upload endpoint,
// then calls this Worker's own /broadcast route to relay the already-saved
// message - authenticated by a shared secret (env.CHAT_BROADCAST_SECRET),
// not a member's bearer token, since accum.se is the caller here, not a
// connected client.

function timingSafeEqual(a, b) {
    if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) return false;
    let result = 0;
    for (let i = 0; i < a.length; i++) {
        result |= a.charCodeAt(i) ^ b.charCodeAt(i);
    }
    return result === 0;
}

export class ChatRoom {
    constructor(state, env) {
        this.state = state;
        this.env = env;
        this.sessions = [];
    }

    async fetch(request) {
        const url = new URL(request.url);
        if (url.pathname === '/broadcast') {
            return this.handleBroadcast(request);
        }
        return this.handleSocket(request);
    }

    async handleBroadcast(request) {
        const secret = request.headers.get('X-Broadcast-Secret') || '';
        if (!this.env.CHAT_BROADCAST_SECRET || !timingSafeEqual(secret, this.env.CHAT_BROADCAST_SECRET)) {
            return new Response('Forbidden', { status: 403 });
        }

        let payload;
        try {
            payload = await request.json();
        } catch (e) {
            return new Response('Bad Request', { status: 400 });
        }

        this.broadcast(payload);
        return new Response('ok');
    }

    async handleSocket(request) {
        if (request.headers.get('Upgrade') !== 'websocket') {
            return new Response('Expected websocket', { status: 426 });
        }

        // Browser JS's WebSocket API can't attach this header - but every
        // real client here is either a native app or this project's own CLI
        // test client, neither of which has that limitation. See CHAT.md's
        // "Authentication on the WebSocket needs no special-casing".
        const authHeader = request.headers.get('Authorization') || '';
        const token = authHeader.startsWith('Bearer ') ? authHeader.slice(7) : null;
        if (!token) {
            return new Response('Unauthorized', { status: 401 });
        }

        let meResponse;
        try {
            meResponse = await fetch(`${this.env.ORIGIN_URL}/api/me.cgi`, {
                headers: { Authorization: `Bearer ${token}` },
            });
        } catch (e) {
            return new Response('Bad Gateway', { status: 502 });
        }
        if (!meResponse.ok) {
            return new Response('Unauthorized', { status: 401 });
        }

        const pair = new WebSocketPair();
        const [client, server] = Object.values(pair);

        server.accept();
        const session = { socket: server, token };
        this.sessions.push(session);

        server.addEventListener('message', (event) => {
            this.handleClientMessage(session, event.data);
        });

        server.addEventListener('close', () => {
            this.sessions = this.sessions.filter((s) => s !== session);
        });

        return new Response(null, { status: 101, webSocket: client });
    }

    async handleClientMessage(session, raw) {
        let data;
        try {
            data = JSON.parse(raw);
        } catch (e) {
            this.sendError(session, 'Ogiltigt meddelande.');
            return;
        }

        // request_id is a client-generated correlation token (see
        // api/chat.cgi's parse_request_id()) - passed straight through to
        // accum.se on the send path (where it doubles as an idempotency
        // key), and echoed back on any error either way so a client with
        // several requests in flight at once can tell which one failed.
        if (data.type === 'message') {
            await this.persistAndBroadcast(
                session, { action: 'send', body: data.body, request_id: data.request_id }, data.request_id);
        } else if (data.type === 'delete') {
            await this.persistAndBroadcast(
                session, { action: 'delete', message_id: data.id, request_id: data.request_id }, data.request_id);
        } else {
            this.sendError(session, 'Okänd åtgärd.', data.request_id);
        }
    }

    async persistAndBroadcast(session, requestBody, requestId) {
        let response;
        try {
            response = await fetch(`${this.env.ORIGIN_URL}/api/chat.cgi`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${session.token}`,
                },
                body: JSON.stringify(requestBody),
            });
        } catch (e) {
            this.sendError(session, 'Kunde inte nå servern.', requestId);
            return;
        }

        let result = null;
        try {
            result = await response.json();
        } catch (e) {
            // No JSON body - handled as a generic failure below.
        }

        if (!response.ok) {
            this.sendError(session, (result && result.error) || 'Något gick fel.', requestId);
            return;
        }

        // No broadcast() call here - accum.se's own trigger_broadcast() (see
        // api/chat.cgi's handle_send()/handle_delete()) already delivers it
        // via this Worker's /broadcast route, for every path alike.
    }

    sendError(session, message, requestId) {
        try {
            session.socket.send(JSON.stringify({ type: 'error', message, request_id: requestId || null }));
        } catch (e) {
            // Session is already gone - nothing to do.
        }
    }

    broadcast(payload) {
        const raw = JSON.stringify(payload);
        for (const session of this.sessions) {
            try {
                session.socket.send(raw);
            } catch (e) {
                // A dead session will get cleaned up by its own close event.
            }
        }
    }
}

export default {
    async fetch(request, env) {
        const url = new URL(request.url);
        if (url.pathname === '/socket' || url.pathname === '/broadcast') {
            const id = env.CHAT_ROOM.idFromName('the-one-chatroom');
            const stub = env.CHAT_ROOM.get(id);
            return stub.fetch(request);
        }
        return new Response('Chat relay worker. Connect to /socket via WebSocket.', { status: 200 });
    },
};
