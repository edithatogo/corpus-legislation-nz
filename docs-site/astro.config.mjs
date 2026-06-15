import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: 'https://edithatogo.github.io',
  base: '/corpus-law-nz/',
  integrations: [
    mdx(),
    sitemap(),
    starlight({
      title: 'Corpus Law NZ',
      description: 'Legal NZ documentation portal for Corpus Law NZ.',
      sidebar: [
        { label: 'Start', items: ['index', 'docs-tooling-audit'] },
      ],
    }),
  ],
});
