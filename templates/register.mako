<%inherit file="base.mako"/>
    <div class="page-container">
        <h1>Registrera medlem</h1>
% if message:
        <div class="alert alert-${'success' if message_kind == 'success' else 'danger'}">${message}</div>
% endif
        <form method="post" action="${base_path}/members/register.cgi" novalidate>
            <div class="mb-3">
                <label class="form-label" for="email">E-post</label>
                <input class="form-control" type="email" id="email" name="email" value="${values.get('email', '')}" required>
            </div>
            <div class="mb-3">
                <label class="form-label" for="password">Lösenord</label>
                <input class="form-control" type="password" id="password" name="password" autocomplete="new-password" required>
            </div>
            <div class="mb-3">
                <label class="form-label" for="instruments">Instrument</label>
                <input class="form-control" type="text" id="instruments" name="instruments" value="${values.get('instruments', '')}">
            </div>
            <div class="mb-3">
                <label class="form-label" for="name">Artistnamn</label>
                <input class="form-control" type="text" id="name" name="name" value="${values.get('name', '')}">
            </div>
            <div class="mb-3 form-check">
                <input class="form-check-input" type="checkbox" id="is_active" name="is_active" ${'checked' if values.get('is_active', True) else ''}>
                <label class="form-check-label" for="is_active">Aktiv medlem</label>
            </div>
            <button class="btn btn-primary" type="submit">Registrera</button>
        </form>
    </div>
