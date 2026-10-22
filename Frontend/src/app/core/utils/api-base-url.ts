/**
 * Resolve API base URL for local and LAN device access.
 * When the SPA is opened via a machine's LAN IP (e.g. http://192.168.x.x:4200)
 * but environment still points at localhost, rewrite the host so phones/tablets
 * on the same network can reach the FastAPI backend.
 */
export function resolveApiBaseUrl(configured: string): string {
  if (typeof window === 'undefined' || !configured) {
    return configured;
  }
  try {
    const url = new URL(configured);
    const pageHost = window.location.hostname;
    const isLoopback =
      url.hostname === 'localhost' || url.hostname === '127.0.0.1';
    const pageIsLoopback =
      pageHost === 'localhost' || pageHost === '127.0.0.1' || pageHost === '';
    if (isLoopback && !pageIsLoopback) {
      url.hostname = pageHost;
      // Keep configured port (backend), strip trailing slash
      return url.toString().replace(/\/$/, '');
    }
  } catch {
    /* keep configured */
  }
  return configured.replace(/\/$/, '');
}
