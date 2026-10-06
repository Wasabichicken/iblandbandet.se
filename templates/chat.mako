<%inherit file="base.mako"/>
    <div id="chat-page" data-token="${chat_token}" data-ws-url="${chat_ws_url}" data-member-id="${member.id}" data-is-admin="${'true' if member.is_admin else 'false'}">
        <div id="chat-messages" aria-live="polite"></div>

        <div id="chat-reply-preview-bar" hidden>
            <div id="chat-reply-preview-text"></div>
            <button type="button" id="chat-reply-preview-cancel" aria-label="Avbryt svar"><i class="bi bi-x-lg"></i></button>
        </div>

        <div id="chat-image-preview" hidden>
            <img id="chat-image-preview-img" alt="">
            <button type="button" id="chat-image-preview-cancel" aria-label="Ta bort bild"><i class="bi bi-x-lg"></i></button>
        </div>

        <form id="chat-form">
            <button type="button" id="chat-attach-btn" class="chat-icon-btn" aria-label="Bifoga bild"><i class="bi bi-image"></i></button>
            <input type="file" id="chat-image-input" accept="image/*" hidden>

            <input type="text" id="chat-text-input" placeholder="Skriv ett meddelande..." autocomplete="off">

            <div class="chat-emoji-wrap">
                <button type="button" id="chat-emoji-btn" class="chat-icon-btn" aria-label="Infoga emoji"><i class="bi bi-emoji-smile"></i></button>
                <div id="chat-emoji-picker" class="chat-emoji-picker" hidden></div>
            </div>

            <button type="submit" id="chat-send-btn" class="chat-icon-btn" aria-label="Skicka"><i class="bi bi-send-fill"></i></button>
        </form>
    </div>

    <script src="${base_path}/static/js/chat.js"></script>
