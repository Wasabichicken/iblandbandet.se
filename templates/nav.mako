    <nav id="sidebar" aria-label="Huvudmeny" aria-hidden="true"\
% if context.get('login_failed', False) or context.get('password_reset', False):
 data-open-on-load="true"\
% endif
>
        <button id="sidebar-close" aria-label="Stäng meny"><i class="bi bi-x-lg"></i></button>
        <ul>
            <li><a href="${base_path}/#om-bandet" class="sidebar-link">Om bandet</a></li>
            <li><a href="${base_path}/#kalender" class="sidebar-link">Kalender</a></li>
            <li><a href="${base_path}/#kontakt" class="sidebar-link">Kontakt</a></li>
        </ul>
% if member is None:
        <form id="sidebar-login" method="post" action="${base_path}/members/login.cgi" novalidate>
            <h2>Logga in</h2>
% if context.get('login_failed', False):
            <p class="sidebar-login-error">Felaktig e-postadress eller lösenord.</p>
% endif
% if context.get('password_reset', False):
            <p class="sidebar-login-success">Lösenordet har bytts. Logga in med ditt nya lösenord.</p>
% endif
            <div class="sidebar-login-field">
                <label for="sidebar-email">E-postadress</label>
                <input type="email" id="sidebar-email" name="email" required>
            </div>
            <div class="sidebar-login-field">
                <label for="sidebar-password">Lösenord</label>
                <input type="password" id="sidebar-password" name="password" required>
            </div>
            <button type="submit">Logga in</button>
        </form>
        <p id="sidebar-login-links">
            <a href="${base_path}/members/forgot_password.cgi" class="sidebar-link">Glömt lösenord?</a>
            <span aria-hidden="true">·</span>
            <a href="${base_path}/members/register.cgi" class="sidebar-link">Registrera dig</a>
        </p>
% else:
        <div id="sidebar-account">
            <p>Inloggad som ${member.email}</p>
            <ul>
                <li><a href="${base_path}/members/profile.cgi" class="sidebar-link">Min profil</a></li>
                <li><a href="${base_path}/members/scores.cgi" class="sidebar-link">Noter</a></li>
% if member.is_admin:
                <li><a href="${base_path}/members/admin.cgi" class="sidebar-link">Admin</a></li>
% endif
                <li><a href="${base_path}/members/logout.cgi" class="sidebar-link">Logga ut</a></li>
            </ul>
        </div>
% endif
    </nav>
    <div id="overlay"></div>

    <header id="header">
        <a id="header-title" href="${base_path}/">iBlandbandet</a>
        <button id="hamburger" aria-label="Öppna meny"><i class="bi bi-list"></i></button>
    </header>
