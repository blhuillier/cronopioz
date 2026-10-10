// @ts-check
import { defineConfig } from 'astro/config';
import { unified } from '@astrojs/markdown-remark';
import rehypeBase from './src/lib/rehype-base.mjs';

// SITE_URL / BASE_PATH are set by the GitHub Actions workflow:
//   blhuillier/cronopioz       -> https://blhuillier.github.io + /cronopioz
//   splazt/splazt.github.io    -> https://splazt.github.io     + /
//   custom domain              -> set repo variables SITE_URL=https://cronopioz.com, BASE_PATH=/
const site = process.env.SITE_URL || 'https://cronopioz.com';
const base = process.env.BASE_PATH || '/';

export default defineConfig({
  site,
  base,
  trailingSlash: 'ignore',
  build: { format: 'directory' },
  markdown: {
    // Root-relative links/images in project bodies ("/images/…", "/projects/…")
    // get the base path prepended, so the site also works under /<repo>/.
    processor: unified({ rehypePlugins: [[rehypeBase, { base }]] }),
  },
});
