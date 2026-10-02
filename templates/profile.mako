<%inherit file="base.mako"/>
    <link href="https://cdn.jsdelivr.net/npm/cropperjs@1.6.2/dist/cropper.min.css" rel="stylesheet">
    <div class="page-container">
        <h1>Min profil</h1>

        <h2>Profilbild</h2>
% if picture_message:
        <div class="alert alert-${'success' if picture_kind == 'success' else 'danger'}">${picture_message}</div>
% endif
        <img class="profile-picture-preview" src="${base_path + (member.profile_picture or '/static/img/avatars/_default.svg')}" alt="Profilbild">

        <div id="avatar-upload-area" data-csrf-token="${csrf_token}">
            <label class="btn btn-outline-primary" for="avatar-file">Ladda upp bild</label>
            <input type="file" id="avatar-file" accept="image/*" hidden>

            <div id="avatar-cropper-wrap" hidden>
                <div class="avatar-cropper-frame">
                    <img id="avatar-crop-image" alt="Beskär profilbild">
                </div>
                <button type="button" id="avatar-save-btn" class="btn btn-primary">Spara bild</button>
                <button type="button" id="avatar-cancel-btn" class="btn btn-secondary">Avbryt</button>
                <span id="avatar-upload-status"></span>
            </div>

% if is_uploaded_photo:
            <form method="post" action="${base_path}/members/profile.cgi" class="mt-2">
                <input type="hidden" name="action" value="remove_picture">
                <input type="hidden" name="csrf_token" value="${csrf_token}">
                <button type="submit" class="btn btn-outline-secondary btn-sm">Ta bort profilbild</button>
            </form>
% endif
        </div>

        <hr class="my-4">

% if profile_message:
        <div class="alert alert-${'success' if profile_kind == 'success' else 'danger'}">${profile_message}</div>
% endif
        <form method="post" action="${base_path}/members/profile.cgi" novalidate>
            <input type="hidden" name="action" value="update_profile">
            <input type="hidden" name="csrf_token" value="${csrf_token}">
            <div class="mb-3">
                <label class="form-label" for="email">E-post</label>
                <input class="form-control" type="email" id="email" name="email" value="${profile_values['email']}" required>
            </div>
            <div class="mb-3">
                <label class="form-label" for="instruments">Instrument</label>
                <input class="form-control" type="text" id="instruments" name="instruments" value="${profile_values['instruments']}">
            </div>
            <div class="mb-3">
                <label class="form-label" for="name">Artistnamn</label>
                <input class="form-control" type="text" id="name" name="name" value="${profile_values['name']}">
            </div>
            <div class="mb-3">
                <label class="form-label" for="description">Beskrivning</label>
                <textarea class="form-control" id="description" name="description" rows="4">${profile_values['description']}</textarea>
            </div>
            <div class="mb-3 form-check">
                <input class="form-check-input" type="checkbox" id="is_active" name="is_active" ${'checked' if profile_values['is_active'] else ''}>
                <label class="form-check-label" for="is_active">Aktiv medlem</label>
            </div>
            <button class="btn btn-primary" type="submit">Spara</button>
        </form>

        <hr class="my-4">

        <h2>Byt lösenord</h2>
% if password_message:
        <div class="alert alert-${'success' if password_kind == 'success' else 'danger'}">${password_message}</div>
% endif
        <form method="post" action="${base_path}/members/profile.cgi" novalidate>
            <input type="hidden" name="action" value="change_password">
            <input type="hidden" name="csrf_token" value="${csrf_token}">
            <div class="mb-3">
                <label class="form-label" for="current_password">Nuvarande lösenord</label>
                <input class="form-control" type="password" id="current_password" name="current_password" required>
            </div>
            <div class="mb-3">
                <label class="form-label" for="new_password">Nytt lösenord</label>
                <input class="form-control" type="password" id="new_password" name="new_password" autocomplete="new-password" required>
            </div>
            <div class="mb-3">
                <label class="form-label" for="confirm_password">Bekräfta nytt lösenord</label>
                <input class="form-control" type="password" id="confirm_password" name="confirm_password" autocomplete="new-password" required>
            </div>
            <button class="btn btn-primary" type="submit">Byt lösenord</button>
        </form>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/cropperjs@1.6.2/dist/cropper.min.js"></script>
    <script src="${base_path}/static/js/avatar-upload.js"></script>
