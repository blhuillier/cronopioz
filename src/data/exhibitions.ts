/**
 * Recent exhibitions shown on the home page (newest first).
 * Add a new show at the top. `project` = folder name in src/content/projects (optional).
 * The full CV lives in src/content/pages/about.md.
 */
export interface Show {
  when: string;          // display date, e.g. "May – Jun 2026"
  title: string;
  where: string;
  kind?: 'solo' | 'group' | 'art fair' | 'curated';
  project?: string;      // links to /projects/<project>
  url?: string;          // external link (venue / press)
}

export const exhibitions: Show[] = [
  {
    when: 'May – Oct 2026',
    title: 'Common Grounds: Networks of Practice',
    where: 'CICA Museum, Gimpo, KR (May – Jun) → CATEDRA, Iași, RO (Sep – Oct)',
    kind: 'group',
    url: 'https://cicamuseum.com/common-grounds-cica-museum-korea-x-catedra-romania/',
  },
  {
    when: 'May – Jun 2026',
    title: 'Felt Seams: What the Tide Erases, the Body Holds',
    where: 'Space &, Crocat House, Incheon, KR',
    kind: 'curated',
    url: 'https://www.koreatimes.co.kr/southkorea/globalcommunity/20260525/incheons-crocat-house-hosts-group-exhibition-featuring-6-korean-global-artists',
  },
  {
    when: '2026',
    title: 'Simulacra & Simulation',
    where: 'Adrián Ibáñez Galería, Bogotá, CO',
    kind: 'group',
  },
  {
    when: 'Apr 2026',
    title: 'Breeze 2026',
    where: 'Seoul, KR',
    kind: 'art fair',
  },
  {
    when: 'Nov 2025',
    title: 'Nostalgia — Incheon Art Show 2025',
    where: 'Songdo ConvenSia, Incheon, KR',
    kind: 'art fair',
  },
  {
    when: 'Jun 2025',
    title: 'Verdant Echoes: Martian Gardener Project',
    where: 'CICA Museum, Gimpo, KR',
    kind: 'solo',
    project: 'martian-gardener-project',
  },
];
