import type { APIRoute } from 'astro';

// Only takes effect at the domain root (production). Test copies under a subpath rely on the
// <meta name="robots" content="noindex"> tag instead, so crawlers must be allowed to read pages.
export const GET: APIRoute = ({ site }) => {
  const noindex = import.meta.env.PUBLIC_NOINDEX === 'true';
  const base = import.meta.env.BASE_URL.replace(/\/?$/, '/');
  const lines = ['User-agent: *', 'Allow: /'];
  if (!noindex && site) lines.push('', `Sitemap: ${new URL(base + 'sitemap.xml', site)}`);
  return new Response(lines.join('\n') + '\n', { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
};
