import { getCollection, type CollectionEntry } from 'astro:content';

export type Project = CollectionEntry<'projects'>;

export const projectPath = (p: Project) => `/projects/${p.data.permalink ?? p.id}`;

export async function allProjects(): Promise<Project[]> {
  const list = await getCollection('projects', ({ data }) => !data.draft);
  return list.sort((a, b) => b.data.date.getTime() - a.data.date.getTime());
}

export async function featuredProjects(): Promise<Project[]> {
  const list = (await allProjects()).filter((p) => p.data.featured);
  return list.sort((a, b) => (a.data.featuredOrder ?? 999) - (b.data.featuredOrder ?? 999));
}
