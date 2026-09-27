<%inherit file="base.mako"/>
<%! from urllib.parse import quote %>
<%
    def entry_href(name):
        # errors='surrogateescape': name may carry raw, un-decodable
        # filename bytes (see fs_display_name in scores.cgi) - this
        # quotes the true original bytes instead of crashing on them.
        return quote((relative_path + '/' + name).strip('/'), errors='surrogateescape')
%>
    <div class="page-container page-container-wide">
        <h1>Noter</h1>

        <nav class="scores-breadcrumb" aria-label="Sökväg">
            <a href="${base_path}/members/scores.cgi"><i class="bi bi-music-note-list"></i> Noter</a>
% for crumb in breadcrumb:
    % if not crumb['is_current']:
            <i class="bi bi-chevron-right"></i> <a href="${base_path}/members/scores.cgi?path=${crumb['href_path']}">${crumb['display_name']}</a>
    % else:
            <i class="bi bi-chevron-right"></i> <span class="scores-breadcrumb-current">${crumb['display_name']}</span>
    % endif
% endfor
        </nav>

% if not entries:
        <p class="scores-empty"><i class="bi bi-folder2-open"></i> Den här mappen är tom.</p>
% else:
        <table class="scores-table">
            <thead>
                <tr>
                    <th>Namn</th>
                    <th class="scores-col-modified">Ändrad</th>
                    <th class="scores-col-size">Storlek</th>
                </tr>
            </thead>
            <tbody>
% for entry in entries:
<%
    href = entry_href(entry['name'])
%>
                <tr>
                    <td class="scores-name-cell">
% if entry['is_dir']:
                        <a href="${base_path}/members/scores.cgi?path=${href}"><i class="bi bi-folder-fill scores-icon scores-icon-folder"></i> ${entry['display_name']}</a>
% elif entry['ext'] == '.pdf':
                        <a href="${base_path}/members/scores.cgi?path=${href}"><i class="bi bi-file-earmark-pdf scores-icon scores-icon-pdf"></i> ${entry['display_name']}</a>
% elif entry['ext'] == '.mp3':
                        <i class="bi bi-file-earmark-music scores-icon scores-icon-audio"></i> ${entry['display_name']}
                        <audio controls src="${base_path}/members/scores.cgi?path=${href}"></audio>
% elif entry['ext'] == '.txt':
                        <a href="${base_path}/members/scores.cgi?path=${href}"><i class="bi bi-file-earmark-text scores-icon scores-icon-text"></i> ${entry['display_name']}</a>
% elif entry['ext'] == '.mscz':
                        <a href="${base_path}/members/scores.cgi?path=${href}"><i class="bi bi-file-earmark-zip scores-icon scores-icon-mscz"></i> ${entry['display_name']}</a>
% endif
                    </td>
                    <td class="scores-col-modified">${entry['modified']}</td>
                    <td class="scores-col-size">${entry['size'] or '–'}</td>
                </tr>
% endfor
            </tbody>
        </table>
% endif
    </div>
