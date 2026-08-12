// Sub-path aware navigation helpers.
//
// Open WebUI can be served behind a reverse proxy under a dynamic sub-path
// (e.g. /service/open-webui). The backend injects the actual prefix into the
// served index.html at request time (both the SvelteKit router base and
// window.__WEBUI_BASE_PATH__), so `base` from $app/paths reflects the real
// prefix at runtime.
//
// Root-relative destinations such as goto('/c/123') or <a href="/admin"> must
// be prefixed with that base, otherwise SvelteKit treats them as external and
// the browser would navigate to the proxy root (404).
import { goto as kitGoto, pushState as kitPushState, replaceState as kitReplaceState } from '$app/navigation';
import { base } from '$app/paths';

export const BASE_PATH: string = base || '';

/**
 * Prefix a root-relative URL with the current sub-path base, if any.
 * Absolute URLs, protocol-relative URLs, hashes, and relative paths are
 * returned untouched.
 */
export function withBase(url: string): string {
	if (!url) {
		return url;
	}
	if (
		url.startsWith('//') ||
		url.startsWith('#') ||
		url.startsWith('http://') ||
		url.startsWith('https://') ||
		url.startsWith('ws://') ||
		url.startsWith('wss://') ||
		url.startsWith('mailto:') ||
		url.startsWith('tel:') ||
		url.startsWith('data:') ||
		url.startsWith('blob:') ||
		url.startsWith('javascript:')
	) {
		return url;
	}
	if (!url.startsWith('/')) {
		// relative path or query/hash-only navigation
		return url;
	}
	if (BASE_PATH && url.startsWith(BASE_PATH)) {
		return url;
	}
	return BASE_PATH + url;
}

/**
 * `goto` wrapper: prefixes root-relative destinations with the base path.
 */
export function goto(url: string | URL, opts?: Parameters<typeof kitGoto>[1]): ReturnType<typeof kitGoto> {
	return kitGoto(typeof url === 'string' ? withBase(url) : url, opts);
}

/**
 * `pushState` wrapper: same base-prefix treatment as `goto`.
 */
export function pushState(url: string | URL, state: Parameters<typeof kitPushState>[1]): void {
	return kitPushState(typeof url === 'string' ? withBase(url) : url, state);
}

/**
 * `replaceState` wrapper: same base-prefix treatment as `goto`.
 */
export function replaceState(url: string | URL, state: Parameters<typeof kitReplaceState>[1]): void {
	return kitReplaceState(typeof url === 'string' ? withBase(url) : url, state);
}

export {
	afterNavigate,
	beforeNavigate,
	disableScrollHandling,
	invalidate,
	invalidateAll,
	onNavigate,
	preloadCode,
	preloadData,
	refreshAll
} from '$app/navigation';
