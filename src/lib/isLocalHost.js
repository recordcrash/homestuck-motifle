// True only when the page is being served from this machine (or the local network), which is how
// development-only affordances decide whether to show themselves. It reads window.location, so it
// is always false on the deployed site and must only be called in the browser.
const LOCAL_HOSTNAMES = ['localhost', '127.0.0.1', '0.0.0.0', '::1', '[::1]'];

export function isLocalHost() {
	if (typeof window === 'undefined') return false;
	const { hostname, protocol } = window.location;
	if (protocol === 'file:') return true;
	if (LOCAL_HOSTNAMES.includes(hostname)) return true;
	// private network ranges, for testing from another device on the same LAN
	return /^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)/.test(hostname) || hostname.endsWith('.local');
}
