// Reverse proxy for www.iblandbandet.se / iblandbandet.se.
//
// The real app lives at https://www.accum.se/~ericj/iblandbandet/ (accum.se
// shared hosting - see CLAUDE.md). This Worker is the origin Cloudflare
// routes iblandbandet.se traffic to: it fetches the equivalent accum.se
// path server-side and strips the /~ericj/iblandbandet prefix back out of
// anything that would otherwise leak it to the browser (redirects, HTML
// links/media, the calendar feed URLs, the one inline base-path script).
// This replaces the old Loopia iframe forward - the browser now talks to
// iblandbandet.se directly and first-party, so Safari ITP / cross-site
// cookie blocking (the login bug) no longer applies at all.
//
// base.mako's injected `window.APP_BASE_PATH` script carries `id="app-base-path"`
// specifically so this Worker can target and replace it reliably (a plain
// text-chunk string replace would be fragile across HTMLRewriter's streaming
// chunk boundaries).
//
// Rewriting covers two shapes the origin's HTML can contain, since
// base_path.py's url()/absolute_url() both get used (see CLAUDE.md):
//   - root-relative: "/~ericj/iblandbandet/..."          (most links)
//   - absolute:      "https://www.accum.se/~ericj/iblandbandet/..." or
//                     "webcal://www.accum.se/~ericj/iblandbandet/..."
//                     (index.cgi's feed_url/webcal_url, which need a real
//                     absolute URI and can't be root-relative)

const ORIGIN_HOST = 'www.accum.se';
const ORIGIN_PREFIX = '/~ericj/iblandbandet';

export default {
    async fetch(request) {
        const url = new URL(request.url);
        const originUrl = new URL(`https://${ORIGIN_HOST}${ORIGIN_PREFIX}${url.pathname}${url.search}`);

        const originHeaders = new Headers(request.headers);
        originHeaders.set('X-Forwarded-Host', url.hostname);
        originHeaders.set('X-Forwarded-Proto', url.protocol.replace(':', ''));

        const hasBody = !(request.method === 'GET' || request.method === 'HEAD');

        const originRequest = new Request(originUrl.toString(), {
            method: request.method,
            headers: originHeaders,
            body: hasBody ? request.body : undefined,
            redirect: 'manual',
            duplex: hasBody ? 'half' : undefined,
        });

        const originResponse = await fetch(originRequest);
        const response = new Response(originResponse.body, originResponse);

        const location = response.headers.get('Location');
        if (location) {
            response.headers.set('Location', rewriteLocation(location, url));
        }

        const contentType = response.headers.get('Content-Type') || '';
        if (contentType.includes('text/html')) {
            return rewriteHtml(response, url);
        }

        return response;
    },
};

// Returns the rewritten value, or null if `value` doesn't reference the
// origin's app path at all (nothing to change).
function rewriteUrlValue(value, requestUrl) {
    if (value.startsWith(ORIGIN_PREFIX)) {
        return value.slice(ORIGIN_PREFIX.length) || '/';
    }
    try {
        const parsed = new URL(value);
        if (parsed.hostname === ORIGIN_HOST && parsed.pathname.startsWith(ORIGIN_PREFIX)) {
            parsed.hostname = requestUrl.hostname;
            if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
                parsed.protocol = requestUrl.protocol;
            }
            parsed.pathname = parsed.pathname.slice(ORIGIN_PREFIX.length) || '/';
            return parsed.toString();
        }
    } catch (e) {
        // Not a parseable/absolute URL - leave it untouched.
    }
    return null;
}

function rewriteLocation(location, requestUrl) {
    const rewritten = rewriteUrlValue(location, requestUrl);
    return rewritten !== null ? rewritten : location;
}

class AttributeRewriter {
    constructor(attributeName, requestUrl) {
        this.attributeName = attributeName;
        this.requestUrl = requestUrl;
    }
    element(element) {
        const value = element.getAttribute(this.attributeName);
        if (!value) return;
        const rewritten = rewriteUrlValue(value, this.requestUrl);
        if (rewritten !== null) {
            element.setAttribute(this.attributeName, rewritten);
        }
    }
}

// Rewrites a plain-text absolute URL wherever it appears verbatim as page
// text (the calendar subscribe box's visible <code>${feed_url}</code>) -
// scoped to a specific selector rather than the whole page, and done as a
// straightforward substring swap per streamed chunk since this is cosmetic
// display text, not something a broken rewrite would functionally break.
class AbsoluteUrlTextRewriter {
    constructor(requestUrl) {
        this.prefix = `https://${ORIGIN_HOST}${ORIGIN_PREFIX}`;
        this.replacement = `${requestUrl.protocol}//${requestUrl.hostname}`;
    }
    text(text) {
        if (text.text.includes(this.prefix)) {
            text.replace(text.text.split(this.prefix).join(this.replacement));
        }
    }
}

class BasePathScriptRewriter {
    element(element) {
        element.setInnerContent('window.APP_BASE_PATH = "";');
    }
}

function rewriteHtml(response, requestUrl) {
    return new HTMLRewriter()
        .on('a[href], link[href]', new AttributeRewriter('href', requestUrl))
        .on('form[action]', new AttributeRewriter('action', requestUrl))
        .on('img[src], script[src], source[src], video[src]', new AttributeRewriter('src', requestUrl))
        .on('.calendar-subscribe-url code', new AbsoluteUrlTextRewriter(requestUrl))
        .on('script#app-base-path', new BasePathScriptRewriter())
        .transform(response);
}
