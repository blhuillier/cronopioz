import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const projects = defineCollection({
  // One folder per project: src/content/projects/<slug>/index.md (+ cover image)
  loader: glob({ pattern: '*/index.md', base: './src/content/projects', generateId: ({ entry }) => entry.split('/')[0] }),
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      date: z.coerce.date(),
      categories: z.array(z.enum(['Art', 'Research', 'Design', 'Infographics'])).default([]),
      tags: z.array(z.string()).default([]),
      featured: z.boolean().default(false),
      featuredOrder: z.number().optional(),
      // URL path under /projects/ (keeps old Squarespace links working). Defaults to the folder name.
      permalink: z.string().optional(),
      excerpt: z.string().default(''),
      cover: image().optional(),
      draft: z.boolean().default(false),
    }),
});

const pages = defineCollection({
  loader: glob({ pattern: '*.md', base: './src/content/pages' }),
  schema: z.object({ title: z.string() }),
});

export const collections = { projects, pages };
