# Secrets live in a sibling file, `.htsecrets` (KEY=VALUE per line, gitignored,
# never committed) - not in Apache's SetEnv/.htaccess, and not in os.environ
# at all. Apache's own built-in "^\.ht" deny rule blocks any dotfile starting
# with ".ht" from ever being served over HTTP regardless of its filesystem
# permissions (confirmed live: even a world-readable .ht* file still 403s) -
# so this file can be locked down to 600, readable only by this account, and
# invisible to every other account on the shared host. CGI scripts run via
# suexec as this account, so they can still read it directly; Apache's own
# worker process (which needs SetEnv values to still work) never needs to.
#
# Deliberately the only place secrets are read from - no os.environ
# fallback - so there's exactly one path to reason about, not two.

import os

_SECRETS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.htsecrets')


def get_secret(name):
    try:
        with open(_SECRETS_PATH) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, _, value = line.partition('=')
                if key.strip() == name:
                    return value.strip()
    except OSError:
        pass
    return None
