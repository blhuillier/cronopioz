/** Build an internal URL that respects the configured base path. */
export function url(path = '/'): string {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${base}${p}` || '/';
}

export const CATEGORIES = ['Art', 'Research', 'Design', 'Infographics'] as const;
export const CATEGORY_LABEL: Record<string, string> = {
  Art: 'Art',
  Research: 'Research',
  Design: 'Design & Dev',
  Infographics: 'Infographics',
};
