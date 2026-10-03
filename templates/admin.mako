<%inherit file="base.mako"/>
<%
    wide = not (edit_member or confirm_delete_member or edit_subtitle or confirm_delete_subtitle)
%>
    <div class="page-container${' page-container-admin' if wide else ''}">
        <h1>Adminpanel</h1>

% if message:
        <div class="alert alert-${'success' if message_kind == 'success' else 'danger'}">${message}</div>
% endif

% if edit_member:
        <h2>Redigera ${edit_member.email}</h2>
        <form method="post" action="${base_path}/members/admin.cgi" novalidate>
            <input type="hidden" name="action" value="update_member">
            <input type="hidden" name="csrf_token" value="${csrf_token}">
            <input type="hidden" name="member_id" value="${edit_member.id}">
            <div class="mb-3">
                <label class="form-label" for="email">E-post</label>
                <input class="form-control" type="email" id="email" name="email" value="${edit_values['email']}" required>
            </div>
            <div class="mb-3">
                <label class="form-label" for="instruments">Instrument</label>
                <input class="form-control" type="text" id="instruments" name="instruments" value="${edit_values['instruments']}">
            </div>
            <div class="mb-3">
                <label class="form-label" for="name">Artistnamn</label>
                <input class="form-control" type="text" id="name" name="name" value="${edit_values['name']}">
            </div>
            <div class="mb-3">
                <label class="form-label" for="description">Beskrivning</label>
                <textarea class="form-control" id="description" name="description" rows="4">${edit_values['description']}</textarea>
            </div>
            <div class="mb-3 form-check">
                <input class="form-check-input" type="checkbox" id="is_active" name="is_active" ${'checked' if edit_values['is_active'] else ''}>
                <label class="form-check-label" for="is_active">Aktiv medlem</label>
            </div>
            <div class="mb-3 form-check">
                <input class="form-check-input" type="checkbox" id="is_admin" name="is_admin" ${'checked' if edit_values['is_admin'] else ''}>
                <label class="form-check-label" for="is_admin">Admin</label>
            </div>
            <button class="btn btn-primary" type="submit">Spara</button>
            <a class="btn btn-secondary" href="${base_path}/members/admin.cgi">Avbryt</a>
        </form>

% elif confirm_delete_member:
        <h2>Ta bort ${confirm_delete_member.email}?</h2>
        <p>Detta går inte att ångra. Medlemmens konto, sessioner och profilbild tas bort permanent.</p>
        <form method="post" action="${base_path}/members/admin.cgi" novalidate>
            <input type="hidden" name="action" value="delete_member">
            <input type="hidden" name="csrf_token" value="${csrf_token}">
            <input type="hidden" name="member_id" value="${confirm_delete_member.id}">
            <button class="btn btn-danger" type="submit">Ja, ta bort</button>
            <a class="btn btn-secondary" href="${base_path}/members/admin.cgi">Avbryt</a>
        </form>

% elif edit_subtitle:
        <h2>Redigera rubrik</h2>
        <form method="post" action="${base_path}/members/admin.cgi" novalidate>
            <input type="hidden" name="action" value="update_subtitle">
            <input type="hidden" name="csrf_token" value="${csrf_token}">
            <input type="hidden" name="subtitle_id" value="${edit_subtitle.id}">
            <div class="mb-3">
                <label class="form-label" for="subtitle">Rubrik</label>
                <input class="form-control" type="text" id="subtitle" name="subtitle" value="${edit_subtitle_value}" required>
            </div>
            <button class="btn btn-primary" type="submit">Spara</button>
            <a class="btn btn-secondary" href="${base_path}/members/admin.cgi">Avbryt</a>
        </form>

% elif confirm_delete_subtitle:
        <h2>Ta bort rubriken "${confirm_delete_subtitle.subtitle}"?</h2>
        <p>Detta går inte att ångra.</p>
        <form method="post" action="${base_path}/members/admin.cgi" novalidate>
            <input type="hidden" name="action" value="delete_subtitle">
            <input type="hidden" name="csrf_token" value="${csrf_token}">
            <input type="hidden" name="subtitle_id" value="${confirm_delete_subtitle.id}">
            <button class="btn btn-danger" type="submit">Ja, ta bort</button>
            <a class="btn btn-secondary" href="${base_path}/members/admin.cgi">Avbryt</a>
        </form>

% else:
        <div class="table-responsive">
            <table class="table table-striped align-middle">
                <thead>
                    <tr>
                        <th></th>
                        <th>E-post</th>
                        <th>Artistnamn</th>
                        <th>Instrument</th>
                        <th>Aktiv</th>
                        <th>Admin</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
% for row in members:
                    <tr>
                        <td><img class="avatar-thumbnail" src="${base_path + avatar_url(row.profile_picture)}" alt=""></td>
                        <td>${row.email}</td>
                        <td>${row.name or '–'}</td>
                        <td>${row.instruments or '–'}</td>
                        <td>${'Ja' if row.is_active else 'Nej'}</td>
                        <td>${'Ja' if row.is_admin else 'Nej'}</td>
                        <td class="text-end">
                            <a class="btn btn-sm btn-outline-primary" href="${base_path}/members/admin.cgi?edit=${row.id}">Redigera</a>
% if row.id != member.id:
                            <a class="btn btn-sm btn-outline-danger" href="${base_path}/members/admin.cgi?confirm_delete=${row.id}">Ta bort</a>
% endif
                        </td>
                    </tr>
% endfor
                </tbody>
            </table>
        </div>

        <hr class="my-4">
        <h2>Rubriker på förstasidan</h2>
        <p>En slumpmässig rubrik visas under "(i)Blandbandet" varje gång startsidan laddas.</p>
        <div class="table-responsive">
            <table class="table table-striped align-middle">
                <thead>
                    <tr>
                        <th>Rubrik</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
% for row in subtitles:
                    <tr>
                        <td>${row.subtitle}</td>
                        <td class="text-end">
                            <a class="btn btn-sm btn-outline-primary" href="${base_path}/members/admin.cgi?edit_subtitle=${row.id}">Redigera</a>
                            <a class="btn btn-sm btn-outline-danger" href="${base_path}/members/admin.cgi?confirm_delete_subtitle=${row.id}">Ta bort</a>
                        </td>
                    </tr>
% endfor
                </tbody>
            </table>
        </div>
        <form method="post" action="${base_path}/members/admin.cgi" class="d-flex align-items-center gap-2" novalidate>
            <input type="hidden" name="action" value="create_subtitle">
            <input type="hidden" name="csrf_token" value="${csrf_token}">
            <label class="form-label mb-0 text-nowrap" for="new-subtitle">Ny rubrik</label>
            <input class="form-control flex-grow-1" type="text" id="new-subtitle" name="subtitle" required>
            <button class="btn btn-primary text-nowrap" type="submit">Lägg till</button>
        </form>
% endif
    </div>
