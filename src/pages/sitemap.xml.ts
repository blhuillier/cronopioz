import type { APIRoute } from 'astro';
import { allProjects, projectPath } from '../lib/projects';
import { CATEGORIES } from '../lib/url';

export const GET: APIRoute = async ({ site }) => {
  const noindex = import.meta.env.PUBLIC_NOINDEX === 'true';
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  const abs = (p: string) => new URL(`${base}${p}`, site).href;
  const projects = noindex ? [] : await allProjects();
  const urls = noindex
    ? []
    : [
        { loc: abs('/'), lastmod: undefined as string | undefined },
        { loc: abs('/projects/'), lastmod: undefined },
        { loc: abs('/archive/'), lastmod: undefined },
        { loc: abs('/about/'), lastmod: undefined },
        ...CATEGORIES.map((c) => ({ loc: abs(`/projects/category/${c}/`), lastmod: undefined })),
        ...projects.map((p) => ({ loc: abs(`${projectPath(p)}/`), lastmod: p.data.date.toISOString().slice(0, 10) })),
      ];
  const body =
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    urls.map((u) => `  <url><loc>${u.loc}</loc>${u.lastmod ? `<lastmod>${u.lastmod}</lastmod>` : ''}</url>`).join('\n') +
    '\n</urlset>\n';
  return new Response(body, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
};
