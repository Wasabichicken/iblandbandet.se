const page = document.getElementById('chat-page');
const basePath = window.APP_BASE_PATH || '';
const token = page.dataset.token;
const wsUrl = page.dataset.wsUrl;
const ownMemberId = parseInt(page.dataset.memberId, 10);
const isAdmin = page.dataset.isAdmin === 'true';

const messagesEl = document.getElementById('chat-messages');
const form = document.getElementById('chat-form');
const textInput = document.getElementById('chat-text-input');
const sendBtn = document.getElementById('chat-send-btn');
const attachBtn = document.getElementById('chat-attach-btn');
const imageInput = document.getElementById('chat-image-input');
const imagePreview = document.getElementById('chat-image-preview');
const imagePreviewImg = document.getElementById('chat-image-preview-img');
const imagePreviewCancel = document.getElementById('chat-image-preview-cancel');
const emojiBtn = document.getElementById('chat-emoji-btn');
const emojiPicker = document.getElementById('chat-emoji-picker');
const replyPreviewBar = document.getElementById('chat-reply-preview-bar');
const replyPreviewText = document.getElementById('chat-reply-preview-text');
const replyPreviewCancel = document.getElementById('chat-reply-preview-cancel');

const EMOJIS = ['😀', '😂', '😍', '😊', '👍', '👎', '❤️', '🎉', '😮', '😢',
                '🙏', '🔥', '😎', '🤔', '👏', '😅', '🥳', '😭', '💪', '🎶'];

let stagedImage = null;
let ws = null;
let pendingOutbox = [];
let replyingTo = null;

// crypto.randomUUID() only exists in a secure context (HTTPS, or
// http://localhost) - this site is also reachable over plain http from a
// LAN IP (e.g. for phone testing), where it's undefined and throws. request_id
// here is just a client-side dedupe/idempotency key, not security-sensitive,
// so a non-crypto fallback is fine.
function generateRequestId() {
    if (window.crypto && typeof window.crypto.randomUUID === 'function') {
        return window.crypto.randomUUID();
    }
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0;
        const v = c === 'x' ? r : (r & 0x3) | 0x8;
        return v.toString(16);
    });
}

// profile_picture from the API always points at /api/avatar.cgi, which
// needs a bearer token neither an <img> tag nor the browser's automatic
// cookie-sending can supply the same way. The website's own session
// cookie *is* sent automatically on a same-origin request, though, so a
// plain website <img src> just needs the website's own gated endpoint
// instead - same file, different (session-cookie-checked) door.
function websiteAvatarUrl(apiProfilePicture) {
    if (!apiProfilePicture) return basePath + '/static/img/avatars/_default.svg';
    const file = new URL(apiProfilePicture, window.location.origin).searchParams.get('file');
    if (!file) return basePath + '/static/img/avatars/_default.svg';
    return basePath + '/members/avatar.cgi?file=' + encodeURIComponent(file);
}

function isNearBottom() {
    return messagesEl.scrollHeight - messagesEl.scrollTop - messagesEl.clientHeight < 80;
}

function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function formatTime(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleString('sv-SE', { hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' });
}

// Shared by the composer's own emoji button and each message's reaction
// picker - same grid of the same EMOJIS, just wired to a different action
// per click (insert into the text input vs. send a reaction).
function buildEmojiGrid(container, onPick) {
    EMOJIS.forEach((emoji) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'chat-emoji-option';
        btn.textContent = emoji;
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            onPick(emoji);
        });
        container.appendChild(btn);
    });
}

function senderLabel(msg) {
    if (msg.member_id === ownMemberId) return 'Du';
    if (msg.name) return msg.name;
    if (msg.member_id === null) return '(borttagen medlem)';
    return 'Medlem #' + msg.member_id;
}

// The full ordered (oldest-first) message list, re-grouped and
// re-rendered from scratch on every change (new message, edit, delete).
// Simpler and easier to get right than patching the DOM incrementally for
// every case that could split, grow, or shrink a cluster - this app's
// message volume makes a full rebuild computationally irrelevant either
// way.
let messages = [];
let editingMessageId = null;

function upsertMessage(msg) {
    const idx = messages.findIndex((m) => m.id === msg.id);
    if (idx === -1) {
        messages.push(msg);
        messages.sort((a, b) => a.id - b.id);
    } else {
        messages[idx] = msg;
    }
}

function removeMessageFromState(id) {
    messages = messages.filter((m) => m.id !== id);
}

function buildBubbleRowEl(msg) {
    const row = document.createElement('div');
    row.className = 'chat-bubble-row';
    row.dataset.id = msg.id;

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';

    // What actually gets appended to the row in place of a lone bubble -
    // a reply additionally wraps the quote card and the bubble in one
    // stack, Messenger-style (quote behind, bubble overlapping its lower
    // edge); a non-reply is just the bubble itself.
    let bubbleContainer = bubble;

    if (msg.reply_to) {
        // The quoted preview is a snapshot the server captured at send
        // time (see api/chat.cgi's build_reply_fields()) - it renders
        // correctly here regardless of whether the original is still in
        // this client's loaded history, was since edited, or was deleted.
        // A separate card from the bubble (not nested inside it) so it
        // survives startEdit()'s bubble.innerHTML swap untouched, and so
        // it can visually sit behind/above the real bubble as its own
        // stacked element.
        const quote = document.createElement('div');
        quote.className = 'chat-reply-preview';
        const quoteName = document.createElement('div');
        quoteName.className = 'chat-reply-preview-name';
        quoteName.textContent = msg.reply_to.name;
        quote.appendChild(quoteName);
        const quoteBody = document.createElement('div');
        quoteBody.className = 'chat-reply-preview-body';
        quoteBody.textContent = msg.reply_to.body || (msg.reply_to.is_image ? '📷 Bild' : '');
        quote.appendChild(quoteBody);
        quote.addEventListener('click', (e) => {
            e.stopPropagation();
            // No-op if the original isn't currently loaded/rendered (out
            // of the loaded history window, or deleted) - graceful by
            // construction, nothing to handle specially.
            const target = document.querySelector('.chat-bubble-row[data-id="' + msg.reply_to.id + '"]');
            if (!target) return;
            target.scrollIntoView({ behavior: 'smooth', block: 'center' });
            target.classList.add('chat-row-highlight');
            setTimeout(() => target.classList.remove('chat-row-highlight'), 1500);
        });

        const stack = document.createElement('div');
        stack.className = 'chat-bubble-stack';
        stack.appendChild(quote);
        stack.appendChild(bubble);
        bubbleContainer = stack;
    }

    if (msg.image_id) {
        const img = document.createElement('img');
        img.className = 'chat-bubble-image';
        img.alt = msg.body || '';
        fetchAuthenticatedImageUrl(msg.image_id).then((url) => { if (url) img.src = url; });
        bubble.appendChild(img);
    }
    if (msg.body) {
        const bodyEl = document.createElement('div');
        bodyEl.className = 'chat-bubble-text';
        bodyEl.textContent = msg.body;
        bubble.appendChild(bodyEl);
    }
    if (msg.edited_at) {
        const edited = document.createElement('span');
        edited.className = 'chat-bubble-edited';
        edited.textContent = '(redigerat)';
        bubble.appendChild(edited);
    }
    if (msg.reactions && msg.reactions.length) {
        // Floats off the bubble's own lower border (see .chat-reactions in
        // style.css) rather than sitting inside its padding, Messenger-
        // style - the row needs a little extra bottom margin to make room
        // for it without crowding the next row.
        row.classList.add('has-reactions');
        const reactionsRow = document.createElement('div');
        reactionsRow.className = 'chat-reactions';
        const byEmoji = new Map();
        msg.reactions.forEach((r) => {
            if (!byEmoji.has(r.emoji)) byEmoji.set(r.emoji, []);
            byEmoji.get(r.emoji).push(r);
        });
        byEmoji.forEach((reactors, emoji) => {
            const mine = reactors.some((r) => r.member_id === ownMemberId);
            const pill = document.createElement('button');
            pill.type = 'button';
            pill.className = 'chat-reaction-pill' + (mine ? ' mine' : '');
            pill.textContent = emoji + ' ' + reactors.length;
            pill.title = reactors
                .map((r) => (r.member_id === ownMemberId ? 'Du' : (r.name || '(borttagen medlem)')))
                .join(', ');
            // Clicking an existing badge is the same toggle/replace action
            // as picking it fresh from the picker - sendReaction() already
            // handles both.
            pill.addEventListener('click', (e) => { e.stopPropagation(); sendReaction(msg, emoji); });
            reactionsRow.appendChild(pill);
        });
        bubble.appendChild(reactionsRow);
    }

    const isOwn = msg.member_id === ownMemberId;

    // Row-level action icons - always visible to every viewer on every
    // row, never hover-revealed (touch devices have no hover state; this
    // mirrors the earlier, deliberate move away from hover-only actions).
    const actions = document.createElement('div');
    actions.className = 'chat-row-actions';

    const replyBtn = document.createElement('button');
    replyBtn.type = 'button';
    replyBtn.className = 'chat-action-icon';
    replyBtn.setAttribute('aria-label', 'Svara');
    replyBtn.innerHTML = '<i class="bi bi-reply-fill"></i>';
    replyBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        startReply(msg);
    });
    actions.appendChild(replyBtn);

    const reactWrap = document.createElement('div');
    reactWrap.className = 'chat-reaction-picker-wrap';
    const reactBtn = document.createElement('button');
    reactBtn.type = 'button';
    reactBtn.className = 'chat-action-icon';
    reactBtn.setAttribute('aria-label', 'Reagera');
    reactBtn.innerHTML = '<i class="bi bi-emoji-smile"></i>';
    const reactPicker = document.createElement('div');
    reactPicker.className = 'chat-reaction-picker';
    reactPicker.hidden = true;
    buildEmojiGrid(reactPicker, (emoji) => {
        reactPicker.hidden = true;
        sendReaction(msg, emoji);
    });
    reactBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const wasHidden = reactPicker.hidden;
        closeAllChatPopups();
        reactPicker.hidden = !wasHidden;
    });
    reactWrap.appendChild(reactBtn);
    reactWrap.appendChild(reactPicker);
    actions.appendChild(reactWrap);

    if (isOwn || isAdmin) {
        // Always-visible "..." menu, not a hover reveal - same hand-rolled
        // show/hide pattern as drive.js's own action menu (plain Bootstrap
        // .dropdown-menu/.show CSS classes, no JS bundle), and critically,
        // not reliant on a mouse hover state that a touch device simply
        // doesn't have. Admins get it on everyone's messages too - the API
        // already allows admin edit/delete of others' messages
        // (api/chat.cgi's handle_edit/handle_delete), this just exposes it.
        const dropdown = document.createElement('div');
        dropdown.className = 'chat-actions-dropdown';

        const toggle = document.createElement('button');
        toggle.type = 'button';
        toggle.className = 'chat-actions-toggle';
        toggle.setAttribute('aria-label', 'Fler alternativ');
        toggle.innerHTML = '<i class="bi bi-three-dots"></i>';
        dropdown.appendChild(toggle);

        const menu = document.createElement('div');
        menu.className = 'dropdown-menu';

        const editBtn = document.createElement('button');
        editBtn.type = 'button';
        editBtn.className = 'dropdown-item';
        editBtn.textContent = 'Redigera';
        editBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            menu.classList.remove('show');
            startEdit(dropdown, bubble, msg);
        });
        menu.appendChild(editBtn);

        const delBtn = document.createElement('button');
        delBtn.type = 'button';
        delBtn.className = 'dropdown-item';
        delBtn.textContent = 'Ta bort';
        delBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            menu.classList.remove('show');
            deleteMessage(msg.id);
        });
        menu.appendChild(delBtn);

        dropdown.appendChild(menu);
        toggle.addEventListener('click', (e) => {
            e.stopPropagation();
            const wasOpen = menu.classList.contains('show');
            closeAllChatPopups();
            if (!wasOpen) menu.classList.add('show');
        });

        actions.appendChild(dropdown);
    }

    // On own (right-aligned) rows the actions sit before the bubble so
    // they land on the inward side, toward the center of the chat rather
    // than the screen edge; on others' (left-aligned) rows, the mirror
    // placement is after the bubble, for the same reason.
    if (isOwn) {
        row.appendChild(actions);
        row.appendChild(bubbleContainer);
    } else {
        row.appendChild(bubbleContainer);
        row.appendChild(actions);
    }
    return row;
}

function closeAllChatPopups() {
    document.querySelectorAll('.chat-actions-dropdown .dropdown-menu.show').forEach((m) => m.classList.remove('show'));
    document.querySelectorAll('.chat-reaction-picker').forEach((p) => { p.hidden = true; });
}

document.addEventListener('click', closeAllChatPopups);

// One group per run of consecutive messages from the same sender: the
// name/time shown once above the first message, the avatar shown once,
// aligned with the bottom (most recent) message - same convention
// Messenger uses.
function buildGroupEl(groupMessages) {
    const first = groupMessages[0];
    const last = groupMessages[groupMessages.length - 1];
    const isOwn = first.member_id === ownMemberId;

    const group = document.createElement('div');
    group.className = 'chat-group' + (isOwn ? ' own' : '');

    const col = document.createElement('div');
    col.className = 'chat-group-col';

    const meta = document.createElement('div');
    meta.className = 'chat-message-meta';
    const nameSpan = document.createElement('span');
    nameSpan.className = 'chat-message-name';
    nameSpan.textContent = senderLabel(first);
    meta.appendChild(nameSpan);
    const timeSpan = document.createElement('span');
    timeSpan.className = 'chat-message-time';
    timeSpan.textContent = formatTime(first.created_at);
    meta.appendChild(timeSpan);
    col.appendChild(meta);

    groupMessages.forEach((msg) => col.appendChild(buildBubbleRowEl(msg)));

    // No avatar on your own messages - Messenger skips it too, since
    // right-alignment and the distinct bubble color already identify them
    // without spending the extra width.
    if (!isOwn) {
        const avatar = document.createElement('img');
        avatar.className = 'chat-avatar';
        avatar.src = websiteAvatarUrl(last.profile_picture);
        avatar.alt = '';
        group.appendChild(avatar);
    }

    group.appendChild(col);
    return group;
}

function renderAll() {
    // Don't tear down an in-progress edit out from under the member typing
    // it just because an unrelated message arrived - the edit's own
    // commit/cancel triggers a fresh renderAll() that catches up anyway.
    if (editingMessageId !== null) return;

    const wasNearBottom = isNearBottom();
    messagesEl.innerHTML = '';
    let i = 0;
    while (i < messages.length) {
        let j = i;
        while (j + 1 < messages.length && messages[j + 1].member_id === messages[i].member_id) j++;
        messagesEl.appendChild(buildGroupEl(messages.slice(i, j + 1)));
        i = j + 1;
    }
    if (wasNearBottom) scrollToBottom();
}

function startEdit(dropdown, bubble, msg) {
    editingMessageId = msg.id;
    dropdown.hidden = true;
    const existingText = msg.body || '';
    bubble.innerHTML = '';
    const editInput = document.createElement('input');
    editInput.type = 'text';
    editInput.className = 'chat-edit-input';
    editInput.value = existingText;
    bubble.appendChild(editInput);
    editInput.focus();
    editInput.setSelectionRange(existingText.length, existingText.length);

    function commit() {
        const newBody = editInput.value.trim();
        editingMessageId = null;
        if (newBody && newBody !== existingText) {
            sendOverSocket({ type: 'edit', id: msg.id, body: newBody, request_id: generateRequestId() });
        } else {
            // No real change (or emptied on a text-only message, which the
            // server would reject anyway) - just redraw as it was.
            renderAll();
        }
    }

    editInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') { e.preventDefault(); commit(); }
        if (e.key === 'Escape') { editingMessageId = null; renderAll(); }
    });
    editInput.addEventListener('blur', commit);
}

function deleteMessage(id) {
    sendOverSocket({ type: 'delete', id, request_id: generateRequestId() });
}

function sendReaction(msg, emoji) {
    // Picking the same emoji you already reacted with toggles it off
    // (emoji: null) - the server enforces this same rule independently
    // (api/chat.cgi's handle_react()), this is just this client's own
    // shortcut to decide which to send.
    const mine = (msg.reactions || []).find((r) => r.member_id === ownMemberId);
    const nextEmoji = mine && mine.emoji === emoji ? null : emoji;
    sendOverSocket({ type: 'reaction', id: msg.id, emoji: nextEmoji, request_id: generateRequestId() });
}

function startReply(msg) {
    replyingTo = {
        id: msg.id,
        name: senderLabel(msg),
        body: msg.body,
        is_image: !!msg.image_id,
    };
    replyPreviewText.textContent = replyingTo.name + ': ' + (replyingTo.body || (replyingTo.is_image ? '📷 Bild' : ''));
    replyPreviewBar.hidden = false;
    textInput.focus();
}

function clearReplyingTo() {
    replyingTo = null;
    replyPreviewBar.hidden = true;
    replyPreviewText.textContent = '';
}

replyPreviewCancel.addEventListener('click', clearReplyingTo);

const imageUrlCache = new Map();

async function fetchAuthenticatedImageUrl(imageId) {
    if (imageUrlCache.has(imageId)) return imageUrlCache.get(imageId);
    try {
        const res = await fetch(basePath + '/api/chat.cgi?image=' + encodeURIComponent(imageId), {
            headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return null;
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        imageUrlCache.set(imageId, url);
        return url;
    } catch (e) {
        return null;
    }
}

async function loadHistory() {
    const res = await fetch(basePath + '/api/chat.cgi?limit=50', {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return;
    const history = await res.json();
    history.slice().reverse().forEach(upsertMessage);
    renderAll();
}

function connectSocket() {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;

    ws = new WebSocket(wsUrl + '?token=' + encodeURIComponent(token));

    ws.addEventListener('open', () => {
        const toSend = pendingOutbox;
        pendingOutbox = [];
        toSend.forEach((payload) => ws.send(JSON.stringify(payload)));
    });

    ws.addEventListener('message', (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'message' || data.type === 'edit' || data.type === 'reaction') {
            upsertMessage(data);
            renderAll();
        } else if (data.type === 'delete') {
            removeMessageFromState(data.id);
            renderAll();
        } else if (data.type === 'error') {
            console.error('Chat error:', data.message);
        }
    });

    ws.addEventListener('close', () => {
        setTimeout(connectSocket, 3000);
    });
}

// Mobile browsers often suspend or silently drop the WebSocket when the tab
// is backgrounded (screen lock, switching apps) without firing a 'close'
// event, so the reconnect above never triggers - reconnecting as soon as the
// page is visible/focused again closes that gap without waiting on it.
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) connectSocket();
});
window.addEventListener('focus', connectSocket);

function sendOverSocket(payload) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(payload));
    } else {
        pendingOutbox.push(payload);
        connectSocket();
    }
}

function setStagedImage(file) {
    stagedImage = file;
    const reader = new FileReader();
    reader.onload = () => {
        imagePreviewImg.src = reader.result;
        imagePreview.hidden = false;
    };
    reader.readAsDataURL(file);
}

function clearStagedImage() {
    stagedImage = null;
    imageInput.value = '';
    imagePreview.hidden = true;
    imagePreviewImg.src = '';
}

attachBtn.addEventListener('click', () => imageInput.click());
imageInput.addEventListener('change', () => {
    if (imageInput.files && imageInput.files[0]) setStagedImage(imageInput.files[0]);
});
imagePreviewCancel.addEventListener('click', clearStagedImage);

emojiBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    emojiPicker.hidden = !emojiPicker.hidden;
});
document.addEventListener('click', () => { emojiPicker.hidden = true; });
if (emojiPicker.children.length === 0) {
    buildEmojiGrid(emojiPicker, (emoji) => {
        const start = textInput.selectionStart || textInput.value.length;
        const end = textInput.selectionEnd || textInput.value.length;
        textInput.value = textInput.value.slice(0, start) + emoji + textInput.value.slice(end);
        textInput.focus();
        textInput.selectionStart = textInput.selectionEnd = start + emoji.length;
    });
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (stagedImage) {
        const body = new FormData();
        body.append('image', stagedImage);
        if (textInput.value.trim()) body.append('body', textInput.value.trim());
        body.append('request_id', generateRequestId());
        if (replyingTo) body.append('reply_to_id', replyingTo.id);
        sendBtn.disabled = true;
        try {
            await fetch(basePath + '/api/chat.cgi', {
                method: 'POST',
                headers: { Authorization: `Bearer ${token}` },
                body,
            });
        } finally {
            sendBtn.disabled = false;
        }
        clearStagedImage();
        textInput.value = '';
        clearReplyingTo();
        return;
    }

    const text = textInput.value.trim();
    if (!text) return;
    sendOverSocket({
        type: 'message',
        body: text,
        reply_to_id: replyingTo && replyingTo.id,
        request_id: generateRequestId(),
    });
    textInput.value = '';
    clearReplyingTo();
});

loadHistory().then(connectSocket);
