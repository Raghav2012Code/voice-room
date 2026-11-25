// @ts-check
const { themes: prismThemes } = require('prism-react-renderer');

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Voice Room',
  tagline: 'Local text to speech. Runs here. Nothing is uploaded.',
  favicon: 'img/favicon.png',
  url: 'https://Raghav2012Code.github.io',
  baseUrl: '/voice-room/',
  organizationName: 'Raghav2012Code',
  projectName: 'voice-room',
  trailingSlash: false,
  onBrokenLinks: 'throw',
  markdown: {
    hooks: {
      onBrokenMarkdownLinks: 'warn',
    },
  },
  i18n: { defaultLocale: 'en', locales: ['en'] },
  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.js',
          editUrl: 'https://github.com/Raghav2012Code/voice-room/tree/master/website/',
        },
        blog: false,
        theme: { customCss: './src/css/custom.css' },
      },
    ],
  ],
  themeConfig: {
    image: 'img/logo.png',
    colorMode: {
      defaultMode: 'dark',
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Voice Room',
      logo: { alt: 'Voice Room', src: 'img/logo.png' },
      items: [
        { type: 'docSidebar', sidebarId: 'docs', position: 'left', label: 'Docs' },
        { to: '/docs/quickstart', label: 'Quickstart', position: 'left' },
        {
          href: 'https://github.com/Raghav2012Code/voice-room',
          label: 'GitHub',
          position: 'right',
        },
        {
          href: 'https://github.com/Raghav2012Code/voice-room/releases/tag/v0.1.0',
          label: 'Download',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            { label: 'Quickstart', to: '/docs/quickstart' },
            { label: 'Adding an engine', to: '/docs/engines/adding-an-engine' },
            { label: 'API reference', to: '/docs/api' },
          ],
        },
        {
          title: 'Project',
          items: [
            { label: 'GitHub', href: 'https://github.com/Raghav2012Code/voice-room' },
            { label: 'Releases', href: 'https://github.com/Raghav2012Code/voice-room/releases' },
            { label: 'License', href: 'https://github.com/Raghav2012Code/voice-room/blob/master/LICENSE' },
          ],
        },
      ],
      copyright: `MIT licensed. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.oneDark,
      darkTheme: prismThemes.oneDark,
      additionalLanguages: ['python', 'bash', 'json', 'rust'],
    },
    tableOfContents: { minHeadingLevel: 2, maxHeadingLevel: 3 },
    mermaid: { theme: { light: 'neutral', dark: 'dark' } },
  },
};

module.exports = config;
