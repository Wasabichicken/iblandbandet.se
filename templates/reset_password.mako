<%inherit file="base.mako"/>
    <div class="page-container">
        <h1>Byt lösenord</h1>
% if message:
        <div class="alert alert-${'success' if message_kind == 'success' else 'danger'}">${message}</div>
% endif
% if token:
        <form method="post" action="${base_path}/members/reset_password.cgi" novalidate>
            <input type="hidden" name="token" value="${token}">
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
% else:
        <p><a href="${base_path}/members/forgot_password.cgi">Begär en ny länk</a></p>
% endif
    </div>
