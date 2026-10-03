<%inherit file="base.mako"/>
    <div class="page-container">
        <h1>Registrera medlem</h1>
% if message:
        <div class="alert alert-${'success' if message_kind == 'success' else 'danger'}">${message}</div>
% endif
        <form method="post" action="${base_path}/members/register.cgi" novalidate>
            <div class="mb-3">
                <label class="form-label" for="email">E-post
                    <span class="info-tooltip">
                        <button type="button" class="info-tooltip-toggle" aria-label="Om detta fält"><i class="bi bi-info-circle"></i></button>
                        <span class="info-tooltip-text">Används endast för direktkontakt med dig, samt inloggning. Endast synlig för administratörer.</span>
                    </span>
                </label>
                <input class="form-control" type="email" id="email" name="email" value="${values.get('email', '')}" required>
            </div>
            <div class="mb-3">
                <label class="form-label" for="password">Lösenord
                    <span class="info-tooltip">
                        <button type="button" class="info-tooltip-toggle" aria-label="Om detta fält"><i class="bi bi-info-circle"></i></button>
                        <span class="info-tooltip-text">Kan aldrig ses eller återskapas av någon, inte ens administratörerna.</span>
                    </span>
                </label>
                <input class="form-control" type="password" id="password" name="password" autocomplete="new-password" required>
            </div>
            <div class="mb-3">
                <label class="form-label" for="instruments">Instrument
                    <span class="info-tooltip">
                        <button type="button" class="info-tooltip-toggle" aria-label="Om detta fält"><i class="bi bi-info-circle"></i></button>
                        <span class="info-tooltip-text">Valfri information. Delas aldrig med personer utanför bandet.</span>
                    </span>
                </label>
                <input class="form-control" type="text" id="instruments" name="instruments" value="${values.get('instruments', '')}">
            </div>
            <div class="mb-3">
                <label class="form-label" for="name">Artistnamn
                    <span class="info-tooltip">
                        <button type="button" class="info-tooltip-toggle" aria-label="Om detta fält"><i class="bi bi-info-circle"></i></button>
                        <span class="info-tooltip-text">Valfri information, endast hur du visas för andra bandmedlemmar.</span>
                    </span>
                </label>
                <input class="form-control" type="text" id="name" name="name" value="${values.get('name', '')}">
            </div>
            <div class="mb-3 form-check">
                <input class="form-check-input" type="checkbox" id="is_active" name="is_active" ${'checked' if values.get('is_active', True) else ''}>
                <label class="form-check-label" for="is_active">Aktiv medlem</label>
            </div>
            <p class="form-text">Genom att registrera dig godkänner du vår <a href="${base_path}/privacy.cgi">integritetspolicy</a>.</p>
            <button class="btn btn-primary" type="submit">Registrera</button>
        </form>
    </div>
