import os
import sys

from mako.lookup import TemplateLookup

from base_path import get_base_path

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_MODULE_DIR = os.path.join(_BASE_DIR, '.mako_modules')

lookup = TemplateLookup(
    directories=[os.path.join(_BASE_DIR, 'templates')],
    module_directory=_MODULE_DIR,
    input_encoding='utf-8',
    default_filters=['h'],
)


def render(template_name, **context):
    template = lookup.get_template(template_name)
    # base_path is environment config (which URL prefix the app is served
    # under), not per-request data, so it's injected here rather than
    # requiring every .cgi script to pass it explicitly - every template
    # needs it for every href/src/action, same reasoning as why 'member'
    # is required but this one isn't.
    context.setdefault('base_path', get_base_path())
    output = template.render(**context)
    _fix_module_permissions()
    # Writing raw bytes to the underlying buffer, not print(), because CGI's
    # stdout encoding is whatever the ambient locale happens to be - on
    # accum.se that's plain ASCII, not UTF-8 (confirmed empirically: any å/ä/ö
    # in the page crashed print() with UnicodeEncodeError there, despite
    # working fine locally where the locale is already UTF-8). Explicit UTF-8
    # bytes sidestep the locale question entirely rather than assuming it.
    sys.stdout.buffer.write(b'Content-Type: text/html; charset=utf-8\n\n')
    sys.stdout.buffer.write(output.encode('utf-8'))
    sys.stdout.buffer.flush()


def _fix_module_permissions():
    # Mako writes compiled modules via tempfile.mkstemp(), which always
    # creates them as mode 600 regardless of umask - both eric (local
    # testing) and www-data (real requests) compile into this same
    # directory, so whichever compiles a template first would otherwise
    # lock the other out from even reading the cached module.
    try:
        for name in os.listdir(_MODULE_DIR):
            if name.endswith('.py'):
                try:
                    os.chmod(os.path.join(_MODULE_DIR, name), 0o664)
                except OSError:
                    pass
    except OSError:
        pass
