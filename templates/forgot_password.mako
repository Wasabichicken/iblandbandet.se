<%inherit file="base.mako"/>
    <div class="page-container">
        <h1>Glömt lösenord</h1>
% if message:
        <div class="alert alert-${'success' if message_kind == 'success' else 'danger'}">${message}</div>
% endif
% if message_kind != 'success':
        <p>Ange din e-postadress så skickar vi instruktioner för att byta lösenord dit.</p>
        <form method="post" action="${base_path}/members/forgot_password.cgi" novalidate>
            <div class="mb-3">
                <label class="form-label" for="email">E-postadress</label>
                <input class="form-control" type="email" id="email" name="email" required>
            </div>
            <button class="btn btn-primary" type="submit">Skicka länk</button>
        </form>
% endif
    </div>
