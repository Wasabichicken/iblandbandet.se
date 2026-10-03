<%inherit file="base.mako"/>
<%
    dir_qs = '&dir=' + str(dir_id) if dir_id else ''
    cancel_href = base_path + '/members/drive.cgi' + ('?dir=' + str(dir_id) if dir_id else '')
%>
    <div class="page-container page-container-wide">
        <h1>Filer</h1>

% if message:
        <div class="alert alert-${'success' if message_kind == 'success' else 'danger'}">${message}</div>
% endif

% if not move_picker:
        <nav class="scores-breadcrumb" aria-label="Sökväg">
            <a href="${base_path}/members/drive.cgi"><i class="bi bi-hdd-fill"></i> Filer</a>
% for crumb in breadcrumb:
    % if not crumb['is_current']:
            <i class="bi bi-chevron-right"></i> <a href="${base_path}/members/drive.cgi?dir=${crumb['id']}">${crumb['name']}</a>
    % else:
            <i class="bi bi-chevron-right"></i> <span class="scores-breadcrumb-current">${crumb['name']}</span>
    % endif
% endfor
        </nav>
% endif

% if confirm_delete:
        <h2>Ta bort "${confirm_delete.name}"?</h2>
        <p>Detta går inte att ångra.</p>
        <form method="post" action="${base_path}/members/drive.cgi" novalidate>
            <input type="hidden" name="action" value="delete">
            <input type="hidden" name="csrf_token" value="${csrf_token}">
            <input type="hidden" name="item_id" value="${confirm_delete.id}">
            <button class="btn btn-danger" type="submit">Ja, ta bort</button>
            <a class="btn btn-secondary" href="${cancel_href}">Avbryt</a>
        </form>
% elif rename_target:
        <h2>Byt namn på "${rename_target.name}"</h2>
        <form method="post" action="${base_path}/members/drive.cgi" novalidate>
            <input type="hidden" name="action" value="rename">
            <input type="hidden" name="csrf_token" value="${csrf_token}">
            <input type="hidden" name="item_id" value="${rename_target.id}">
% if dir_id:
            <input type="hidden" name="dir" value="${dir_id}">
% endif
            <div class="mb-3">
                <label class="form-label" for="rename-name">Namn</label>
                <input class="form-control" type="text" id="rename-name" name="name" value="${rename_target.name}" required>
            </div>
            <button class="btn btn-primary" type="submit">Spara</button>
            <a class="btn btn-secondary" href="${cancel_href}">Avbryt</a>
        </form>
% elif move_picker:
        <h2>Flytta "${move_picker['item'].name}"</h2>
        <nav class="scores-breadcrumb" aria-label="Sökväg">
            <a href="${base_path}/members/drive.cgi?move=${move_picker['item'].id}${dir_qs}"><i class="bi bi-hdd-fill"></i> Filer</a>
% for crumb in move_picker['breadcrumb']:
    % if not crumb['is_current']:
            <i class="bi bi-chevron-right"></i> <a href="${base_path}/members/drive.cgi?move=${move_picker['item'].id}&picker_dir=${crumb['id']}${dir_qs}">${crumb['name']}</a>
    % else:
            <i class="bi bi-chevron-right"></i> <span class="scores-breadcrumb-current">${crumb['name']}</span>
    % endif
% endfor
        </nav>

% if not move_picker['folders']:
        <p class="scores-empty"><i class="bi bi-folder2-open"></i> Inga mappar här.</p>
% else:
        <ul class="list-group mb-3">
% for folder in move_picker['folders']:
            <li class="list-group-item">
                <a href="${base_path}/members/drive.cgi?move=${move_picker['item'].id}&picker_dir=${folder['id']}${dir_qs}"><i class="bi bi-folder-fill scores-icon scores-icon-folder"></i> ${folder['name']}</a>
            </li>
% endfor
        </ul>
% endif

        <form method="post" action="${base_path}/members/drive.cgi" class="d-inline" novalidate>
            <input type="hidden" name="action" value="move">
            <input type="hidden" name="csrf_token" value="${csrf_token}">
            <input type="hidden" name="item_id" value="${move_picker['item'].id}">
% if move_picker['picker_dir_id']:
            <input type="hidden" name="new_parent_id" value="${move_picker['picker_dir_id']}">
% endif
% if dir_id:
            <input type="hidden" name="dir" value="${dir_id}">
% endif
            <button class="btn btn-primary" type="submit">Välj den här mappen</button>
        </form>
        <a class="btn btn-secondary" href="${cancel_href}">Avbryt</a>
% elif change_owner_target:
        <h2>Byt ägare för "${change_owner_target.name}"</h2>
        <form method="post" action="${base_path}/members/drive.cgi" novalidate>
            <input type="hidden" name="action" value="change_owner">
            <input type="hidden" name="csrf_token" value="${csrf_token}">
            <input type="hidden" name="item_id" value="${change_owner_target.id}">
% if dir_id:
            <input type="hidden" name="dir" value="${dir_id}">
% endif
            <div class="mb-3">
                <label class="form-label" for="change-owner-select">Ny ägare</label>
                <select class="form-select" id="change-owner-select" name="new_owner_id" required>
% for candidate in all_members:
                    <option value="${candidate.id}" ${'selected' if candidate.id == change_owner_target.owner_id else ''}>${candidate.email}</option>
% endfor
                </select>
            </div>
            <button class="btn btn-primary" type="submit">Spara</button>
            <a class="btn btn-secondary" href="${cancel_href}">Avbryt</a>
        </form>
% else:
        <div class="drive-toolbar">
            <form method="post" action="${base_path}/members/drive.cgi" class="d-flex align-items-center gap-2" novalidate>
                <input type="hidden" name="action" value="create_folder">
                <input type="hidden" name="csrf_token" value="${csrf_token}">
% if dir_id:
                <input type="hidden" name="parent_id" value="${dir_id}">
% endif
                <input class="form-control" type="text" name="name" placeholder="Ny mapp" required>
                <button class="btn btn-outline-primary text-nowrap" type="submit"><i class="bi bi-folder-plus"></i> Skapa mapp</button>
            </form>
            <form method="post" action="${base_path}/members/drive.cgi" enctype="multipart/form-data" class="d-flex align-items-center gap-2" novalidate>
                <input type="hidden" name="action" value="upload">
                <input type="hidden" name="csrf_token" value="${csrf_token}">
% if dir_id:
                <input type="hidden" name="parent_id" value="${dir_id}">
% endif
                <input class="form-control" type="file" name="file" required>
                <button class="btn btn-primary text-nowrap" type="submit"><i class="bi bi-upload"></i> Ladda upp</button>
            </form>
        </div>

        <div class="drive-filter-bar">
            <label for="drive-type-filter">Typ</label>
            <select id="drive-type-filter" class="form-select form-select-sm">
                <option value="all">Alla typer</option>
                <option value="folder">Mappar</option>
                <option value="pdf">PDF</option>
                <option value="txt">Text</option>
                <option value="svg">SVG</option>
                <option value="png">PNG</option>
                <option value="mp3">MP3</option>
                <option value="eps">EPS</option>
                <option value="other">Övrigt</option>
            </select>
            <label for="drive-date-filter">Ändrad</label>
            <select id="drive-date-filter" class="form-select form-select-sm">
                <option value="all">Alla datum</option>
                <option value="week">Senaste veckan</option>
                <option value="month">Senaste månaden</option>
                <option value="year">Senaste året</option>
            </select>
        </div>

% if not entries and dir_id is None:
        <p class="scores-empty"><i class="bi bi-folder2-open"></i> Den här mappen är tom.</p>
% else:
        <table class="scores-table drive-table" id="drive-table">
            <thead>
                <tr>
                    <th>Namn</th>
                    <th class="drive-col-owner">Ägare</th>
                    <th class="scores-col-modified">Ändrad</th>
                    <th class="scores-col-size">Storlek</th>
                    <th></th>
                </tr>
            </thead>
            <tbody>
% if dir_id is not None:
                <tr class="drive-parent-row" data-item-id="${parent_dir_id if parent_dir_id else ''}" data-is-directory="true">
                    <td class="scores-name-cell">
                        <a href="${base_path}/members/drive.cgi${'?dir=' + str(parent_dir_id) if parent_dir_id else ''}"><i class="bi bi-arrow-90deg-up scores-icon scores-icon-folder"></i> ..</a>
                    </td>
                    <td class="drive-col-owner"></td>
                    <td class="scores-col-modified"></td>
                    <td class="scores-col-size"></td>
                    <td class="text-end"></td>
                </tr>
% endif
% for entry in entries:
<%
    entry_manageable = member.id == entry['owner_id'] or member.is_admin
%>
                <tr data-type="${'folder' if entry['is_directory'] else (entry['ext'] if entry['ext'] in ('pdf', 'txt', 'svg', 'png', 'mp3', 'eps') else 'other')}" data-created="${entry['created_iso']}" data-item-id="${entry['id']}" data-is-directory="${'true' if entry['is_directory'] else 'false'}" data-owned="${'true' if entry_manageable else 'false'}" draggable="true">
                    <td class="scores-name-cell">
% if entry['is_directory']:
                        <a href="${base_path}/members/drive.cgi?dir=${entry['id']}"><i class="bi ${entry['icon']} scores-icon ${entry['color_class']}"></i> ${entry['name']}</a>
% else:
                        <a href="${base_path}/members/drive.cgi?download=${entry['id']}"><i class="bi ${entry['icon']} scores-icon ${entry['color_class']}"></i> ${entry['name']}</a>
% endif
                    </td>
                    <td class="drive-col-owner">
% if entry['owner_id']:
                        <img class="avatar-thumbnail" src="${base_path + avatar_url(entry['profile_picture'])}" alt="">
% endif
                    </td>
                    <td class="scores-col-modified">${entry['created']}</td>
                    <td class="scores-col-size">${entry['size'] or '–'}</td>
                    <td class="text-end">
% if entry_manageable or not entry['is_directory']:
                        <div class="dropdown drive-actions-dropdown">
                            <button class="btn btn-sm btn-outline-secondary drive-actions-toggle" type="button" aria-haspopup="true" aria-expanded="false">
                                <i class="bi bi-three-dots-vertical"></i>
                            </button>
                            <div class="dropdown-menu dropdown-menu-end">
% if entry_manageable:
                                <a class="dropdown-item" href="${base_path}/members/drive.cgi?rename=${entry['id']}${dir_qs}">Byt namn</a>
                                <a class="dropdown-item" href="${base_path}/members/drive.cgi?move=${entry['id']}${dir_qs}">Flytta till…</a>
% endif
% if not entry['is_directory']:
                                <form method="post" action="${base_path}/members/drive.cgi" class="drive-dropdown-form">
                                    <input type="hidden" name="action" value="copy">
                                    <input type="hidden" name="csrf_token" value="${csrf_token}">
                                    <input type="hidden" name="item_id" value="${entry['id']}">
% if dir_id:
                                    <input type="hidden" name="dir" value="${dir_id}">
% endif
                                    <button class="dropdown-item" type="submit">Gör en kopia</button>
                                </form>
% endif
% if member.is_admin:
                                <a class="dropdown-item" href="${base_path}/members/drive.cgi?change_owner=${entry['id']}${dir_qs}">Byt ägare</a>
% endif
% if entry_manageable:
                                <a class="dropdown-item text-danger" href="${base_path}/members/drive.cgi?confirm_delete=${entry['id']}${dir_qs}">Ta bort</a>
% endif
                            </div>
                        </div>
% endif
                    </td>
                </tr>
% endfor
            </tbody>
        </table>
% endif

        <form method="post" action="${base_path}/members/drive.cgi" id="drive-dragdrop-move-form" hidden>
            <input type="hidden" name="action" value="move">
            <input type="hidden" name="csrf_token" value="${csrf_token}">
            <input type="hidden" name="item_id" id="drive-dragdrop-item-id">
            <input type="hidden" name="new_parent_id" id="drive-dragdrop-new-parent-id">
% if dir_id:
            <input type="hidden" name="dir" value="${dir_id}">
% endif
        </form>
% endif
    </div>
    <script src="${base_path}/static/js/drive.js"></script>
