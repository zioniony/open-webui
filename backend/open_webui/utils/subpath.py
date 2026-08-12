"""Reverse-proxy sub-path (X-Forwarded-Prefix) support.

Open WebUI can be served behind a reverse proxy under a *dynamic* sub-path
(e.g. ``/service/open-webui``). nginx strips the prefix before forwarding, so
the backend always sees root-relative paths such as ``/api/v1/...`` while the
browser must use ``/service/open-webui/api/v1/...``.

This module:

* validates ``X-Forwarded-Prefix`` and exposes it via :func:`get_forwarded_prefix`;
* injects it into the ASGI ``root_path`` so ``request.base_url`` (used by OAuth
  redirects and other absolute-URL generation) already contains the prefix;
* rewrites ``Location`` headers of root-relative redirects so they keep the
  prefix (models.py favicon redirects, legacy RedirectMiddleware, ...);
* rewrites the served SPA ``index.html`` so all asset URLs, the SvelteKit
  router ``base`` and ``window.__WEBUI_BASE_PATH__`` reflect the prefix.

When no ``X-Forwarded-Prefix`` header is present (direct access to the port),
everything behaves exactly as before.
"""

from __future__ import annotations

import json
import re
from typing import Any

from starlette.datastructures import Headers

_FORWARDED_PREFIX_RE = re.compile(r'^/[A-Za-z0-9._~\-/]*$')


def get_forwarded_prefix(scope: dict[str, Any]) -> str:
    """Return the validated sub-path prefix from the ASGI scope, or ''.

    The prefix must start with ``/``, contain only URL-path-safe characters,
    contain no ``//`` and no ``..`` path segments. A trailing slash is
    stripped (``/service/open-webui/`` -> ``/service/open-webui``).
    """
    if scope.get('type') not in ('http', 'websocket'):
        return ''

    headers = Headers(scope=scope)
    raw = headers.get('x-forwarded-prefix')
    if not raw:
        return ''

    raw = raw.strip()
    if not _FORWARDED_PREFIX_RE.match(raw) or '//' in raw:
        return ''
    if any(segment == '..' for segment in raw.split('/')):
        return ''

    prefix = raw.rstrip('/')
    return '' if prefix == '/' else prefix


# Root-absolute asset paths found in the generated SPA index.html. The leading
# slash is consumed by the regex so the replacement can insert the prefix.
_ASSET_ROOT_RE = re.compile(
    r'''(["'(= ])/((?:static|_app|manifest\.json|assets|pyodide|favicon)(?:/[^"'\s)]*)?)'''
)


def rewrite_spa_index_html(html: str, prefix: str) -> str:
    """Rewrite the built ``index.html`` for a given sub-path prefix."""
    # 1) Let client-side code (and pyodide sandboxes) know the base path.
    injected = f'<script>window.__WEBUI_BASE_PATH__={json.dumps(prefix)};</script>'
    if '<head>' in html:
        html = html.replace('<head>', f'<head>{injected}', 1)
    else:
        html = injected + html

    # 2) SvelteKit reads the router base from this inline object at startup:
    #    __sveltekit_1qbk3qd = { base: "" } -> { base: "/service/open-webui" }
    html = re.sub(r'(base\s*:\s*)""', rf'\1{json.dumps(prefix)}', html, count=1)

    # 3) Prefix root-absolute asset URLs (modulepreloads, imports, favicon,
    #    splash images, manifest, ...) so they are fetched under the prefix.
    html = _ASSET_ROOT_RE.sub(lambda m: f'{m.group(1)}{prefix}/{m.group(2)}', html)
    return html


class SubPathMiddleware:
    """ASGI middleware that applies the forwarded sub-path to every request.

    Must be installed outermost (added last) so it wraps compression, CORS and
    all other middleware: it sets ``root_path`` on the scope and rewrites
    root-relative ``Location`` headers on responses.
    """

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        prefix = get_forwarded_prefix(scope)
        if prefix and scope.get('type') == 'http':
            raw_path = scope.get('path', '')
            # /ws/* is handled by python-socketio, which reads scope["path"]
            # directly to identify the socket endpoint. nginx strips the
            # prefix for those requests, so leave the scope untouched (both
            # the WebSocket upgrade and the HTTP polling transport).
            if raw_path.startswith('/ws'):
                await self.app(scope, receive, send)
                return

            # Standard ASGI "root path" semantics (same as uvicorn
            # --root-path): the scope carries BOTH root_path and a path that
            # includes the prefix. Starlette's router strips root_path before
            # matching, so routes keep working, Mount/StaticFiles resolve
            # child paths correctly, and request.base_url already includes the
            # prefix (used by OAuth redirects and other absolute URLs).
            #
            # Websocket scopes are left untouched: nginx strips the prefix and
            # python-socketio reads scope["path"] directly to identify the
            # /ws/socket.io endpoint.
            scope = dict(scope)
            scope['root_path'] = prefix
            path = raw_path
            if not path.startswith(prefix):
                scope['path'] = prefix + path

            async def send_with_prefix(message: dict[str, Any]) -> None:
                if message['type'] == 'http.response.start':
                    headers = list(message.get('headers', []))
                    rewritten = False
                    for idx, (name, value) in enumerate(headers):
                        if name.lower() == b'location':
                            location = value.decode('latin-1')
                            if (
                                location.startswith('/')
                                and not location.startswith('//')
                                and not location.startswith(prefix)
                            ):
                                headers[idx] = (
                                    name,
                                    (prefix + location).encode('latin-1'),
                                )
                                rewritten = True
                    if rewritten:
                        message = {**message, 'headers': headers}
                await send(message)

            await self.app(scope, receive, send_with_prefix)
            return

        await self.app(scope, receive, send)
